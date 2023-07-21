import struct
import ctypes
import os

import windows
import windows.utils as utils

from .native_exec import simple_x86 as x86
from .native_exec import simple_x64 as x64

from windows.native_exec.nativeutils import GetProcAddress64, GetProcAddress32

from windows.dbgprint import dbgprint


def perform_manual_getproc_loadlib_32(target, dll_name):
    dll = "KERNEL32.DLL\x00".encode("utf-16-le")
    api = "LoadLibraryA\x00"
    dll_to_load = dll_name + "\x00"

    RemoteManualLoadLibray = x86.MultipleInstr()
    code = RemoteManualLoadLibray
    code += x86.Mov("ECX", x86.mem("[ESP + 4]"))
    code += x86.Push(x86.mem("[ECX + 4]"))
    code += x86.Push(x86.mem("[ECX]"))
    code += x86.Call(":FUNC_GETPROCADDRESS32")
    code += x86.Push(x86.mem("[ECX + 8]"))
    code += x86.Call("EAX") # LoadLibrary
    code += x86.Pop("ECX")
    code += x86.Pop("ECX")
    code += x86.Ret()

    RemoteManualLoadLibray += GetProcAddress32

    with target.allocated_memory(0x1000) as addr:
        addr2 = addr + len(dll)
        addr3 = addr2 + len(api)
        addr4 = addr3 + len(dll_to_load)

        target.write_memory(addr, dll)
        target.write_memory(addr2, api)
        target.write_memory(addr3, dll_to_load)
        target.write_qword(addr4, addr)
        target.write_qword(addr4 + 4, addr2)
        target.write_qword(addr4 + 0x8, addr3)

        t = target.execute(RemoteManualLoadLibray.get_code(), addr4)
        t.wait()
    return True

def perform_manual_getproc_loadlib_64(target, dll_name):
    dll = "KERNEL32.DLL\x00".encode("utf-16-le")
    api = "LoadLibraryA\x00"
    dll_to_load = dll_name + "\x00"

    RemoteManualLoadLibray = x64.MultipleInstr()
    code = RemoteManualLoadLibray
    code += x64.Mov("R15", "RCX")
    code += x64.Mov("RCX", x64.mem("[R15 + 0]"))
    code += x64.Mov("RDX", x64.mem("[R15 + 8]"))
    code += x64.Call(":FUNC_GETPROCADDRESS64")
    code += x64.Mov("RCX", x64.mem("[R15 + 0x10]"))
    code += x64.Push("RCX")
    code += x64.Push("RCX")
    code += x64.Push("RCX")
    code += x64.Call("RAX") # LoadLibrary
    code += x64.Pop("RCX")
    code += x64.Pop("RCX")
    code += x64.Pop("RCX")
    code += x64.Ret()

    RemoteManualLoadLibray += GetProcAddress64

    with target.allocated_memory(0x1000) as addr:
        addr2 = addr + len(dll)
        addr3 = addr2 + len(api)
        addr4 = addr3 + len(dll_to_load)

        target.write_memory(addr, dll)
        target.write_memory(addr2, api)
        target.write_memory(addr3, dll_to_load)
        target.write_qword(addr4, addr)
        target.write_qword(addr4 + 8, addr2)
        target.write_qword(addr4 + 0x10, addr3)

        t = target.execute(RemoteManualLoadLibray.get_code(), addr4)
        t.wait()
    return True


def load_dll_in_remote_process(target, dll_name):
    rpeb = target.peb
    if rpeb.Ldr:
        # LDR est parcourable, ca va etre deja plus simple..
        modules = rpeb.modules
        if any(mod.name == dll_name for mod in modules):
            # DLL already loaded
            dbgprint("DLL already present in target", "DLLINJECT")
            return True
        k32 = [mod for mod in modules if mod.name.lower() == "kernel32.dll"]
        if k32:
            # We have kernel32 \o/
            k32 = k32[0]
            try:
                load_libraryA = k32.pe.exports["LoadLibraryA"]
            except KeyError:
                raise ValueError("Kernel32 have no export <LoadLibraryA> (wtf)")

            with target.allocated_memory(0x1000) as addr:
                target.write_memory(addr, dll_name + "\x00")
                t = target.create_thread(load_libraryA, addr)
                t.wait()
            dbgprint("DLL Injected via LoadLibray", "DLLINJECT")
            return True
    # Hardcore mode
    # We don't have k32 or PEB->Ldr
    # Go inject a GetProcAddress(LoadLib) + LoadLib shellcode :D
    if target.bitness == 32:
        return perform_manual_getproc_loadlib_32(target, dll_name)
    return perform_manual_getproc_loadlib_64(target, dll_name)

python_function_32_bits = {}
# 32 to 32 injection
def generate_python_exec_shellcode_32(target, PYCODE_ADDR, PyDll):
    if not python_function_32_bits:
        pymodule = [mod for mod in target.peb.modules if mod.name == PyDll][0]
        Py_exports = pymodule.pe.exports
        python_function_32_bits["PyEval_InitThreads"] = Py_exports["PyEval_InitThreads"]
        python_function_32_bits["Py_IsInitialized"] = Py_exports["Py_IsInitialized"]
        python_function_32_bits["PyGILState_Release"] = Py_exports["PyGILState_Release"]
        python_function_32_bits["PyGILState_Ensure"] = Py_exports["PyGILState_Ensure"]
        python_function_32_bits["PyEval_SaveThread"] = Py_exports["PyEval_SaveThread"]
        python_function_32_bits["Py_Initialize"] = Py_exports["Py_Initialize"]
        python_function_32_bits["PyRun_SimpleString"] = Py_exports["PyRun_SimpleString"]
    Py_exports = python_function_32_bits
    PyEval_InitThreads = Py_exports["PyEval_InitThreads"]
    Py_IsInitialized = Py_exports["Py_IsInitialized"]
    PyGILState_Release = Py_exports["PyGILState_Release"]
    PyGILState_Ensure = Py_exports["PyGILState_Ensure"]
    PyEval_SaveThread = Py_exports["PyEval_SaveThread"]
    Py_Initialize = Py_exports["Py_Initialize"]
    PyRun_SimpleString = Py_exports["PyRun_SimpleString"]

    code = x86.MultipleInstr()
    code += x86.Mov('EAX', Py_IsInitialized)
    code += x86.Call('EAX')
    code += x86.Mov("EDI", "EAX")
    code += x86.Cmp("EAX", 0)
    code += x86.Jnz(":DO_ENSURE")
    # Python Initilisation code
    # init multithread (for other injection)
    code +=     x86.Mov('EAX', PyEval_InitThreads)
    code +=     x86.Call('EAX')
    code +=     x86.Mov('EAX', Py_Initialize)
    code +=     x86.Call('EAX')
    code += x86.Label(":DO_ENSURE")
    code += x86.Mov('EAX', PyGILState_Ensure)
    code += x86.Call('EAX')
    code += x86.Push('EAX')
    code += x86.Push(PYCODE_ADDR)
    code += x86.Mov('EAX', PyRun_SimpleString)
    code += x86.Call('EAX')
    code += x86.Mov("ESI", "EAX")
    code += x86.Mov('EAX', PyGILState_Release)
    code += x86.Call('EAX')
    code += x86.Pop('EAX')
    code += x86.Cmp("EDI", 0)
    code += x86.Jnz(":RETURN")
    # If PyEval_InitThreads was called (init done in this thread)
    # We must release the GIL
    code +=     x86.Mov('EAX', PyEval_SaveThread)
    code +=     x86.Call('EAX')
    code += x86.Label(":RETURN")
    code += x86.Mov("EAX", "ESI")
    code += x86.Pop("EDI")
    code += x86.Ret()
    return code.get_code()


python_function_64_bits = {}
# 64 to 64 injection
def generate_python_exec_shellcode_64(target, PYCODE_ADDR, PyDll):
    if not python_function_64_bits:
        pymodule = [mod for mod in target.peb.modules if mod.name == PyDll][0]
        Py_exports = pymodule.pe.exports
        python_function_64_bits["PyEval_InitThreads"] = Py_exports["PyEval_InitThreads"]
        python_function_64_bits["Py_IsInitialized"] = Py_exports["Py_IsInitialized"]
        python_function_64_bits["PyGILState_Release"] = Py_exports["PyGILState_Release"]
        python_function_64_bits["PyGILState_Ensure"] = Py_exports["PyGILState_Ensure"]
        python_function_64_bits["PyEval_SaveThread"] = Py_exports["PyEval_SaveThread"]
        python_function_64_bits["Py_Initialize"] = Py_exports["Py_Initialize"]
        python_function_64_bits["PyRun_SimpleString"] = Py_exports["PyRun_SimpleString"]
    Py_exports = python_function_64_bits
    PyEval_InitThreads = Py_exports["PyEval_InitThreads"]
    Py_IsInitialized = Py_exports["Py_IsInitialized"]
    PyGILState_Release = Py_exports["PyGILState_Release"]
    PyGILState_Ensure = Py_exports["PyGILState_Ensure"]
    PyEval_SaveThread = Py_exports["PyEval_SaveThread"]
    Py_Initialize = Py_exports["Py_Initialize"]
    PyRun_SimpleString = Py_exports["PyRun_SimpleString"]

    Reserve_space_for_call = x64.MultipleInstr([x64.Push('RDI')] * 4)
    Clean_space_for_call = x64.MultipleInstr([x64.Pop('RDI')] * 4)
    code = x64.MultipleInstr()
    # Do stack alignement
    code += x64.Push('RCX')
    code += Reserve_space_for_call
    code += x64.Mov('RAX', Py_IsInitialized)
    code += x64.Call('RAX')
    code += x64.Mov("RDI", "RAX")
    code += x64.Cmp("RAX", 0)
    code += x64.Jnz(":DO_ENSURE")
    code +=     x64.Mov('RAX', PyEval_InitThreads)
    code +=     x64.Call('RAX')
    code +=     x64.Mov('RAX', Py_Initialize)
    code +=     x64.Call('RAX')
    code += x64.Label(":DO_ENSURE")
    code += x64.Mov('RAX', PyGILState_Ensure)
    code += x64.Call('RAX')
    code += x64.Mov('R15', 'RAX')
    code += x64.Mov('RAX', PyRun_SimpleString)
    code += x64.Mov('RCX', PYCODE_ADDR)
    code += x64.Call('RAX')
    code += x64.Mov('RCX', 'R15')
    code += x64.Mov('R15', 'RAX')
    code += x64.Mov('RAX', PyGILState_Release)
    code += x64.Call('RAX')
    code += x64.Cmp("RDI", 0)
    code += x64.Jnz(":RETURN")
    # If PyEval_InitThreads was called (init done in this thread)
    # We must release the GIL
    code +=     x64.Mov('RAX', PyEval_SaveThread)
    code +=     x64.Call('RAX')
    code += x64.Label(":RETURN")
    code += Clean_space_for_call
    # Remove stack alignement
    code += x64.Pop('RCX')
    code += x64.Mov("RAX", "R15")
    code += x64.Ret()
    return code.get_code()


def inject_python_command(target, code_injected, PYDLL):
    """Postulate: PYDLL is already loaded in target process"""
    PYCODE = code_injected + "\x00"
    # TODO: free this (how ? when ?)
    remote_addr = target.virtual_alloc(len(PYCODE) + 0x100)
    target.write_memory(remote_addr, PYCODE)
    SHELLCODE_ADDR = remote_addr + len(PYCODE)

    if target.bitness == 32:
        shellcode_generator = generate_python_exec_shellcode_32
    else:
        shellcode_generator = generate_python_exec_shellcode_64

    shellcode = shellcode_generator(target, remote_addr, PYDLL)
    target.write_memory(SHELLCODE_ADDR, shellcode)
    return SHELLCODE_ADDR


def validate_python_dll_presence_on_disk(process):
    if windows.current_process.bitness == process.bitness:
        return True
    if windows.current_process.bitness == 32 and process.bitness == 64:
        with windows.utils.DisableWow64FsRedirection():
            if not os.path.exists(r"C:\Windows\system32\python27.dll"):
                raise ValueError("Could not find Python DLL to inject")
            return True
    if windows.current_process.bitness == 64 and process.bitness == 32:
        if not os.path.exists(r"C:\Windows\SysWOW64\python27.dll"):
            raise ValueError("Could not find Python DLL to inject")
        return True
    raise NotImplementedError("Unknown bitness")

def execute_python_code(process, code):
    validate_python_dll_presence_on_disk(process)
    load_dll_in_remote_process(process, "python27.dll")
    addr = inject_python_command(process, code, "python27.dll")
    t = process.create_thread(addr, 0)
    return t


retrieve_exc = r"""
import traceback
import sys
addr = {0}
txt = "".join(traceback.format_exception(sys.last_type, sys.last_value, sys.last_traceback))
import ctypes

size = ctypes.c_uint.from_address(addr)
size.value = len(txt)
buff = (ctypes.c_char * len(txt)).from_address(addr + ctypes.sizeof(ctypes.c_uint))
buff[:] = txt
"""

def retrieve_last_exception_data(process):
    with process.allocated_memory(0x1000) as mem:
        execute_python_code(process, retrieve_exc.format(mem))
        size = struct.unpack("<I", process.read_memory(mem, ctypes.sizeof(ctypes.c_uint)))[0]
        data = process.read_memory(mem + ctypes.sizeof(ctypes.c_uint), size)
    return data

class RemotePythonError(Exception):
    pass

def safe_execute_python(process, code):
    t = execute_python_code(process, code)
    t.wait() # Wait terminaison of the thread
    if t.exit_code == 0:
        return True
    if t.exit_code != 0xffffffff:
        raise ValueError("Unknown exit code {0}".format(hex(t.exit_code)))
    data = retrieve_last_exception_data(process)
    raise RemotePythonError(data)


