#!/usr/bin/python

"""
This is a dead simple worker that occasionally checks the Django database for
work - when it finds some, it kicks off the createVM process. Upon completion
the sandbox request of interest is updated.
"""
import sqlite3
import sys
import time
import createvm

def connectDB():
    return sqlite3.connect("../db.sqlite3")

def getJob(conn):
    """
    Get the next available sandbox request and set its status to pending.
    """
    cur = conn.execute("SELECT cocreate_sandboxrequest.id, cocreate_sandboxrequest.sandbox_id, cocreate_sandboxrequest.requested_by_id, cocreate_sandboxrequest.sandbox_name, cocreate_sandboxtemplate.recipe FROM cocreate_sandboxrequest, cocreate_sandboxtemplate WHERE cocreate_sandboxrequest.request_status = 'app' AND cocreate_sandboxrequest.template_id = cocreate_sandboxtemplate.id LIMIT 1")
    try:
        request_id, sandbox_id, requested_by_id, sandbox_name, sandbox_recipe = cur.fetchone()
        conn.execute("UPDATE cocreate_sandboxrequest SET request_status = 'pen' WHERE id = ?", (request_id,))
        conn.commit()
    except TypeError:
        return None
            
    return {"request_id": request_id, "sandbox_id": sandbox_id, "requested_by_id": requested_by_id, "sandbox_name": sandbox_name, "sandbox_recipe": sandbox_recipe}

def dispatchJob(job):
    """
    Call out to the VM creation code to set things up. This also generates a FQDN and IP address.
    """
    
    # Eventually, we want to allow the user to specify the desired hostname in the request.
    hostname = "cocreate%d" % (job['sandbox_id'])
    
    if getMode() == "dev":
        return True, {
            "job": job,
            "fqdn": hostname + ".isee.mitre.org",
            "ip_address": "127.0.0.1"
        }
    else:
        try:
            ip, fqdn, err_message, progress = createvm.createVM(job['request_id'], hostname, job['sandbox_recipe'], updateProgress)
            if ip and fqdn:
                return True, {
                    "job": job,
                    "fqdn": fqdn,
                    "ip_address": ip,
                }
            else:
                return False, {
                    "job": job,
                    "err_message": err_message,
                    "progress": progress
                }
        except Exception as e:
            print(e)
            return False, {
                "job": job,
                "err_message": "Error while creating sandbox",
                "progress": 0
            }
    
def updateSandbox(conn, success, jobResults):
    """
    Update the database with the results of the VM creation request.
    """
    if success:
        conn.execute("UPDATE cocreate_sandbox SET hostname = ?, ip_address = ? WHERE id = ?", (jobResults['fqdn'], jobResults['ip_address'], jobResults['job']['sandbox_id']))
    else:
        conn.execute("UPDATE cocreate_sandboxrequest SET request_status = ?, request_progress = ?, request_progress_msg = ? WHERE id = ?", ('err', jobResults['progress'], jobResults['err_message'], jobResults['job']['request_id']))
        conn.execute(
            "INSERT INTO cocreate_notification (added_at, read, msg, related_model_type, related_model_id, owner_id, progress, object_name, error) values (datetime('now'), 0, ?, 'srq', ?, ?, ?, ?, 1)",
            (jobResults['err_message'], jobResults['job']['request_id'], jobResults['job']['requested_by_id'], jobResults['progress'], jobResults['job']['sandbox_name'])
        )
    conn.commit()

def updateProgress(request_id, percent_complete, message, url=None):
    """
    Update the progress of the sandbox request in the database.
    """
   
    cur = conn.execute("SELECT sandbox_id, sandbox_name, requested_by_id FROM cocreate_sandboxrequest WHERE id = ?", (request_id,))
    try:
        sandbox_id, sandbox_name, requested_by_id = cur.fetchone()
    except TypeError:
        raise LookupError('specified request not found')
    
    if percent_complete < 0 or percent_complete > 100:
        raise ValueError('percent_complete out of range')
    
    if len(message) > 100:
        raise ValueError('message too long')
    
    if percent_complete == 100:
        conn.execute("UPDATE cocreate_sandboxrequest SET request_status = ?, request_progress = ?, request_progress_msg = ? WHERE id = ?", ('avl', percent_complete, message, request_id))
    else:
        conn.execute("UPDATE cocreate_sandboxrequest SET request_progress = ?, request_progress_msg = ? WHERE id = ?", (percent_complete, message, request_id))
        
    conn.execute(
        "INSERT INTO cocreate_notification (added_at, read, msg, related_model_type, related_model_id, owner_id, progress, object_name, error) values (datetime('now'), 0, ?, 'srq', ?, ?, ?, ?, 0)",
        (message, request_id, requested_by_id, percent_complete, sandbox_name)
    )
    
    if url:
        conn.execute("UPDATE cocreate_sandbox SET url = ? WHERE id = ?", (url,sandbox_id ))

    conn.commit()
        
    return

def getMode():
    mode = "test"
    
    if len(sys.argv) > 1:
        if sys.argv[-1].lower() in ['dev', 'test', 'prod']:
            mode = sys.argv[-1].lower()
    return mode
    
if __name__ == "__main__":
    
    
    print("Starting Co-Create background worker...")
    conn = connectDB()
    
    # For dev testing
    if getMode() == "dev":
        percent_complete = 25
        
    try:
        while True:
            job = getJob(conn)
            
            if job is not None:
                
                print( "Got a job:" )
                print( "\tRequest id: %d" % (job['request_id']) )
                print( "\tSandbox id: %d" % (job['sandbox_id']) )
                
                success, jobResults = dispatchJob(job)
                updateSandbox(conn, success, jobResults)
               
                if success: 
                    print( "\tFQDN: %s" % (jobResults['fqdn']) )
                    print( "\tIP Address: %s" % (jobResults['ip_address']) )
                else:
                    print("\tError: " + jobResults['err_message'])
                
                ##############################################
                # For dev testing
                if getMode() == "dev":
                    msg = 'Request ' + str(percent_complete) + '% complete'
                    if percent_complete == 100:
                        updateProgress(job['request_id'], percent_complete, msg, 'http://cocreate14.isee.mitre.org/geoq')
                        percent_complete = 25
                    else:
                        updateProgress(job['request_id'], percent_complete, msg)
                        percent_complete += 25
                ##############################################
            
            time.sleep(10)
    finally:
        print('Closing database connection')
        conn.close()
