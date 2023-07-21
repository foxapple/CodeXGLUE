#!/usr/bin/env python
import os, sys, argparse, subprocess, binascii
from cPickle import *
from pbcore.io.FastaIO import FastaReader
from pbcore.io.FastqIO import FastqReader, FastqWriter
from pbtools.pbtranscript.Cluster import Cluster
from pbtools.pbtranscript.ClusterOptions import IceOptions, SgeOptions, \
            IceQuiverHQLQOptions
from pbtools.pbtranscript.PBTranscriptOptions import add_cluster_arguments
from pbtools.pbtranscript.ice.IceUtils import convert_fofn_to_fasta
from pbtools.pbtranscript.counting import get_read_count_from_collapsed as sp
from bisect import bisect_right

def sep_flnc_by_primer(flnc_filename, root_dir, output_filename='isoseq_flnc.fasta'):
    """
    Separate flnc fasta by primer. Useful for targeted sequencing.
    ex: make <root_dir>/primer0/isoseq_flnc.fasta ... etc ...
    """
    def get_primer(r):
        for x in r.name.split(';'):
            if x.startswith('primer='):
                return x.split('=')[1]

    primers = set()
    for r in FastaReader(flnc_filename):
        p = get_primer(r)
        primers.add(p)

    handles = {}
    for p in primers:
        dirname = os.path.join(root_dir, "primer{0}".format(p))
        if os.path.exists(dirname):
            print >> sys.stderr, "WARNING: {0} already exists.".format(dirname)
        else:
            os.makedirs(dirname)
        handles[p] = open(os.path.join(dirname, output_filename), 'w')

    for r in FastaReader(flnc_filename):
        p = get_primer(r)
        handles[p].write(">{0}\n{1}\n".format(r.name, r.sequence))

    for f in handles.itervalues(): f.close()
    primers = list(primers)
    primers.sort(key=lambda x: int(x))
    return [handles[x] for x in primers]


def sep_flnc_by_size(flnc_filename, root_dir, bin_size_kb=1, bin_manual=None, output_filename='isoseq_flnc.fasta'):
    """
    Separate flnc fasta into different size bins
    ex: make <root_dir>/0to2k/isoseq_flnc.fasta ... etc ...

    If <bin_manual> (ex: (0, 2, 4, 12)) is given, <bin_size_kb> is ignored.
    """
    # first check min - max size range
    min_size = 0
    max_size = 0
    for r in FastaReader(flnc_filename):
        seqlen = len(r.sequence)
        min_size = min(min_size, seqlen)
        max_size = max(max_size, seqlen)
    
    min_size_kb = min_size/1000
    max_size_kb = max_size/1000 + (1 if max_size%1000 > 1 else 0)
    if bin_manual is not None:
        if bin_manual[0] > min_size_kb:
            raise Exception, "Min sequence length is {0} kb, below the bin!".format(min_size)
        if bin_manual[-1] < max_size_kb:
            raise Exception, "Max sequence length is {0} kb, above the bin!".format(max_size)
        bins = bin_manual
    else:
        bins = range(min_size_kb, max_size_kb+1, bin_size_kb)

    print >> sys.stderr, bins

    handles = {}
    for i in xrange(len(bins)-1):
        dirname = os.path.join(root_dir, "{0}to{1}kb".format(bins[i], bins[i+1]))
        if os.path.exists(dirname):
            print >> sys.stderr, "WARNING: {0} already exists.".format(dirname)
        else:
            os.makedirs(dirname)
        handles[i] = open(os.path.join(dirname, output_filename), 'w')

    max_bin = len(bins)-1
    for r in FastaReader(flnc_filename):
        kb_size = len(r.sequence)/1000
        i = min(max_bin, max(0, bisect_right(bins, kb_size)-1))
        handles[i].write(">{0}\n{1}\n".format(r.name, r.sequence))
        print >> sys.stderr, "putting {0} in {1}".format(len(r.sequence), handles[i].name)
    for h in handles.itervalues(): h.close()
    names = [handles[i].name for i in xrange(len(bins)-1)]
#    return names
    return filter(lambda x: os.stat(x).st_size > 0, names)

def combine_quiver_results(split_dirs, output_dir, hq_filename, lq_filename, tofu_prefix=''):
    """
    For each size bin result, ex: clusterOut/0to2k/all.quiveredXXX.fastq
    combine it together, remember to add a prefix (ex: i0|c12, i1|c13/....)
    """
    prefix_dict_hq  = {}
    prefix_dict_lq = {}
    fout_hq = FastqWriter(os.path.join(output_dir, 'all_sizes.quivered_hq.fastq'))
    fout_lq = FastqWriter(os.path.join(output_dir, 'all_sizes.quivered_lq.fastq'))
    for i,d in enumerate(split_dirs):
        file_hq = os.path.join(d, hq_filename) #'all_quivered_hq.100_30_0.99.fastq')
        file_lq = os.path.join(d, lq_filename) #'all_quivered_lq.fastq')
        print >> sys.stderr, "Adding prefix i{0}| to {1},{2}...".format(i, file_hq, file_lq)
        prefix_dict_hq["i{0}HQ".format(i)] = d
        prefix_dict_lq["i{0}LQ".format(i)] = d
        for r in FastqReader(file_hq):
            _name_ = "i{i}HQ{p}|{n}".format(p=tofu_prefix, i=i, n=r.name)
            fout_hq.writeRecord(_name_, r.sequence, r.quality)
        for r in FastqReader(file_lq):
            _name_ = "i{i}LQ{p}|{n}".format(p=tofu_prefix, i=i, n=r.name)
            fout_lq.writeRecord(_name_, r.sequence, r.quality)
    fout_hq.close()
    fout_lq.close()
    print >> sys.stderr, "HQ quivered output combined to:", fout_hq.file.name
    print >> sys.stderr, "LQ quivered output combined to:", fout_lq.file.name
    return fout_hq.file.name,fout_lq.file.name,prefix_dict_hq,prefix_dict_lq


def run_collapse_sam(fastq_filename, gmap_db_dir, gmap_db_name, cpus=24):
    """
    Wrapper for running collapse script
    (a) run GMAP
    (b) sort GMAP sam
    (c) run collapse_isoforms_by_sam
    """
    cmd = "gmap -D {d} -d {name} -n 0 -t {cpus} -f samse {fq} > {fq}.sam 2> {fq}.sam.log".format(\
            d=gmap_db_dir, name=gmap_db_name, cpus=cpus, fq=fastq_filename)
    print >> sys.stderr, "CMD:", cmd
    subprocess.check_call(cmd, shell=True)
    cmd = "sort -k 3,3 -k 4,4n {fq}.sam > {fq}.sorted.sam".format(fq=fastq_filename)
    print >> sys.stderr, "CMD:", cmd
    subprocess.check_call(cmd, shell=True) 
    cmd = "collapse_isoforms_by_sam.py --input {fq} --fq -s {fq}.sorted.sam -o {fq}.5merge".format(\
            fq=fastq_filename)
    print >> sys.stderr, "CMD:", cmd
    subprocess.check_call(cmd, shell=True)
    return fastq_filename + '.5merge.collapsed'

def get_abundance(collapse_prefix, prefix_dict, output_prefix, restricted_movies=None):
    cid_info = sp.read_group_filename(collapse_prefix + ".group.txt", is_cid=True,\
            sample_prefixes=prefix_dict.keys())

    fl_pickles = []
    nfl_pickles = []
    for i, d in prefix_dict.iteritems():
        file = os.path.join(d, 'output/final.pickle')
        if not os.path.exists(file):
            raise Exception, "Expected FL pickle file {0} but not found!".format(file)
        fl_pickles.append((i, file))
        file = os.path.join(d, 'output/map_noFL/nfl.all.partial_uc.pickle')
        if not os.path.exists(file):
            raise Exception, "Expected nFL pickle file {0} but not found!".format(file)
        nfl_pickles.append((i, file))

    sp.output_read_count_FL(cid_info, fl_pickles, output_prefix + '.read_stat.txt', 'w', restricted_movies=restricted_movies)
    sp.output_read_count_nFL(cid_info, nfl_pickles, output_prefix + '.read_stat.txt', 'a', restricted_movies=restricted_movies)
    sp.make_abundance_file(output_prefix + '.read_stat.txt', output_prefix + '.abundance.txt', restricted_movies=restricted_movies)
    print >> sys.stderr, "Abundance file written to", output_prefix + '.abundance.txt'

def tofu_wrap_main():
    parser = argparse.ArgumentParser()
    add_cluster_arguments(parser)

    parser.add_argument("--bin_size_kb", default=1, type=int, help="Bin size by kb (default: 1)")
    parser.add_argument("--bin_manual", default=None, help="Bin manual (ex: (1,2,3,5)), overwrites bin_size_kb")
    parser.add_argument("--bin_by_primer", default=False, action="store_true", help="Instead of binning by size, bin by primer (overwrites --bin_size_kb and --bin_manual)")
    parser.add_argument("--gmap_name", default="hg19", help="GMAP DB name (default: hg19)")
    parser.add_argument("--gmap_db", default="/home/UNIXHOME/etseng/share/gmap_db_new/", help="GMAP DB location (default: /home/UNIXHOME/etseng/share/gmap_db_new/)")
    parser.add_argument("--output_seqid_prefix", type=str, default=None, help="Output seqid prefix. If not given, a random ID is generated")
    args = parser.parse_args()

    # #################################################################
    # SANITY CHECKS
    if not args.quiver:
        print >> sys.stderr, "--quiver must be turned on for tofu_wrap. Quit."
        sys.exit(-1)
    if args.nfl_fa is None:
        print >> sys.stderr, "--nfl_fa must be provided for tofu_wrap. Quit."
        sys.exit(-1)
    if not os.path.exists(args.gmap_db):
        print >> sys.stderr, "GMAP DB location not valid: {0}. Quit.".format(args.gmap_db)
        sys.exit(-1)
    if not os.path.exists(os.path.join(args.gmap_db, args.gmap_name)):
        print >> sys.stderr, "GMAP name not valid: {0}. Quit.".format(args.gmap_name)
        sys.exit(-1)
    # #################################################################


    tofu_prefix = binascii.b2a_hex(os.urandom(3)) if args.output_seqid_prefix is None else output_seqid_prefix

    ice_opts = IceOptions(cDNA_size=args.cDNA_size,
            quiver=args.quiver)
    sge_opts = SgeOptions(unique_id=args.unique_id,
            use_sge=args.use_sge,
            max_sge_jobs=args.max_sge_jobs,
            blasr_nproc=args.blasr_nproc,
            quiver_nproc=args.quiver_nproc)
    ipq_opts = IceQuiverHQLQOptions(qv_trim_5=args.qv_trim_5,
            qv_trim_3=args.qv_trim_3,
            hq_quiver_min_accuracy=args.hq_quiver_min_accuracy,
            hq_isoforms_fa=args.hq_isoforms_fa,
            hq_isoforms_fq=args.hq_isoforms_fq,
            lq_isoforms_fa=args.lq_isoforms_fa,
            lq_isoforms_fq=args.lq_isoforms_fq)
    # ex: all_quivered_hq.100_30_0.99.fastq
    quiver_hq_filename = "all_quivered_hq.{0}_{1}_{2:.2f}.fastq".format(\
            args.qv_trim_5,args.qv_trim_3,args.hq_quiver_min_accuracy)
    quiver_lq_filename = "all_quivered_lq.fastq"

    # (1) separate input flnc into size bins or primers
    if args.bin_by_primer:
        split_files = sep_flnc_by_primer(args.flnc_fa, args.root_dir)
    else:
        bin_manual = eval(args.bin_manual) if args.bin_manual is not None else None
        split_files = sep_flnc_by_size(args.flnc_fa, args.root_dir, bin_size_kb=args.bin_size_kb, bin_manual=bin_manual)
    print >> sys.stderr, "split input {0} into {1} bins".format(args.flnc_fa, len(split_files))

    # (2) if fasta_fofn already is there, use it; otherwise make it first
    if args.quiver and args.fasta_fofn is None:
        print >> sys.stderr, "Making fasta_fofn now"
        nfl_dir = os.path.abspath(os.path.join(args.root_dir, "fasta_fofn_files"))
        if not os.path.exists(nfl_dir):
            os.makedirs(nfl_dir)
        args.fasta_fofn = os.path.join(nfl_dir, 'input.fasta.fofn')
        print >> sys.stderr, "fasta_fofn", args.fasta_fofn
        print >> sys.stderr, "nfl_dir", nfl_dir
        convert_fofn_to_fasta(fofn_filename=args.bas_fofn,
                            out_filename=args.fasta_fofn,
                            fasta_out_dir=nfl_dir,
                            cpus=args.blasr_nproc)
    else:
        if not os.path.exists(args.fasta_fofn):
            raise Exception, "fasta_fofn {0} does not exist!".format(args.fasta_fofn)
        for line in open(args.fasta_fofn):
            file = line.strip()
            if len(file) > 0 and not os.path.exists(file):
                raise Exception, "File {0} does not exists in {1}".format(file, args.fasta_fofn)

    # (3) run ICE/Quiver (the whole thing), providing the fasta_fofn
    split_dirs = []
    for cur_file in split_files:
        cur_dir = os.path.dirname(cur_file)
        split_dirs.append(cur_dir)
        cur_out_cons = os.path.join(cur_dir, args.consensusFa)
        
        hq_quiver = os.path.join(cur_dir, quiver_hq_filename)
        if os.path.exists(hq_quiver):
            print >> sys.stderr, "{0} already exists. SKIP!".format(hq_quiver)
            continue
        print >> sys.stderr, "running ICE/Quiver on", cur_dir
        obj = Cluster(root_dir=cur_dir,
                flnc_fa=cur_file,
                nfl_fa=args.nfl_fa,
                bas_fofn=args.bas_fofn,
                ccs_fofn=args.ccs_fofn,
                fasta_fofn=args.fasta_fofn,
                out_fa=cur_out_cons,
                sge_opts=sge_opts,
                ice_opts=ice_opts,
                ipq_opts=ipq_opts,
                report_fn=args.report_fn,
                summary_fn=args.summary_fn,
                nfl_reads_per_split=args.nfl_reads_per_split)
        obj.run()

    combined_dir = os.path.join(args.root_dir, 'combined')
    if not os.path.exists(combined_dir):
        os.makedirs(combined_dir)
    # (4) combine quivered HQ/LQ results
    hq_filename, lq_filename, hq_pre_dict, lq_pre_dict = \
            combine_quiver_results(split_dirs, combined_dir, quiver_hq_filename, quiver_lq_filename, \
            prefix=tofu_prefix)
    with open('combined.hq_lq_pre_dict.pickle', 'w') as f:
        dump({'HQ': hq_pre_dict, 'LQ': lq_pre_dict}, f)
    # (5) collapse quivered HQ results
    collapse_prefix_hq = run_collapse_sam(hq_filename, args.gmap_db, args.gmap_name, cpus=args.blasr_nproc)
    # (6) make abundance 
    get_abundance(collapse_prefix_hq, hq_pre_dict, collapse_prefix_hq)
    # Now do it for LQ (turned OFF for now)
    #collapse_prefix_lq = run_collapse_sam(lq_filename, '/home/UNIXHOME/etseng/share/gmap_db_new/', 'hg19', 24)
    #get_abundance(collapse_prefix_lq, lq_pre_dict, collapse_prefix_lq)

if __name__ == "__main__":
    tofu_wrap_main()
