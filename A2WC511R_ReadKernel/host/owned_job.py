"""Private Windows process-tree lifetime helper; no provider/transport operations."""
import sys
sys.dont_write_bytecode=True
import ctypes as c
from ctypes import wintypes as w
import msvcrt,os,subprocess,time

k=c.WinDLL('kernel32',use_last_error=True)
class _STARTUP(c.Structure):
    _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),
              ('x',w.DWORD),('y',w.DWORD),('xsize',w.DWORD),('ysize',w.DWORD),('xchars',w.DWORD),('ychars',w.DWORD),
              ('fill',w.DWORD),('flags',w.DWORD),('show',w.WORD),('reserved_size',w.WORD),('reserved2',c.c_void_p),
              ('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
class _PROCESS(c.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
class _LIMIT(c.Structure):
    _fields_=[('process_time',c.c_longlong),('job_time',c.c_longlong),('flags',w.DWORD),('min_working',c.c_size_t),
              ('max_working',c.c_size_t),('active_limit',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class _IO(c.Structure):_fields_=[(name,c.c_ulonglong) for name in ['read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes']]
class _EXTENDED(c.Structure):
    _fields_=[('basic',_LIMIT),('io',_IO),('process_memory',c.c_size_t),('job_memory',c.c_size_t),('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
class _ACCOUNTING(c.Structure):
    _fields_=[('user',c.c_longlong),('kernel',c.c_longlong),('period_user',c.c_longlong),('period_kernel',c.c_longlong),
              ('faults',w.DWORD),('total_processes',w.DWORD),('active_processes',w.DWORD),('terminated_processes',w.DWORD)]
for name,args,result in [
    ('CreateJobObjectW',[c.c_void_p,w.LPCWSTR],w.HANDLE),
    ('SetInformationJobObject',[w.HANDLE,c.c_int,c.c_void_p,w.DWORD],w.BOOL),
    ('QueryInformationJobObject',[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p],w.BOOL),
    ('AssignProcessToJobObject',[w.HANDLE,w.HANDLE],w.BOOL),
    ('TerminateJobObject',[w.HANDLE,w.UINT],w.BOOL),
    ('TerminateProcess',[w.HANDLE,w.UINT],w.BOOL),
    ('CreateProcessW',[w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(_STARTUP),c.POINTER(_PROCESS)],w.BOOL),
    ('ResumeThread',[w.HANDLE],w.DWORD),('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD),
    ('GetExitCodeProcess',[w.HANDLE,c.POINTER(w.DWORD)],w.BOOL),('CloseHandle',[w.HANDLE],w.BOOL)]:
    fn=getattr(k,name);fn.argtypes=args;fn.restype=result

def _ok(value,message):
    if not value:raise OSError(c.get_last_error(),message)

def _active(job):
    info=_ACCOUNTING();_ok(k.QueryInformationJobObject(job,1,c.byref(info),c.sizeof(info),None),'Query owned job')
    return info.active_processes

def _run_owned_job(args,cwd,env,log_path,timeout_seconds):
    """Create suspended, assign kill-on-close job, then resume; always drain job."""
    if not 0<timeout_seconds<=7200:raise ValueError('Bounded owned-process timeout required')
    job=k.CreateJobObjectW(None,None);_ok(job,'Create private job')
    proc=_PROCESS();assigned=False
    try:
        limits=_EXTENDED();limits.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        _ok(k.SetInformationJobObject(job,9,c.byref(limits),c.sizeof(limits)),'Set kill-on-close')
        command=c.create_unicode_buffer(subprocess.list2cmdline([str(x) for x in args]))
        environment=c.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(env.items(),key=lambda x:x[0].upper()))+'\0\0')
        with open(log_path,'xb') as log,open(os.devnull,'rb') as null:
            stdout=msvcrt.get_osfhandle(log.fileno());stdin=msvcrt.get_osfhandle(null.fileno())
            os.set_handle_inheritable(stdout,True);os.set_handle_inheritable(stdin,True)
            startup=_STARTUP();startup.cb=c.sizeof(startup);startup.flags=0x101;startup.show=0
            startup.stdin=stdin;startup.stdout=stdout;startup.stderr=stdout
            try:
                # CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW
                _ok(k.CreateProcessW(str(args[0]),command,None,None,True,0x08000404,environment,str(cwd),c.byref(startup),c.byref(proc)),'Create suspended owned launcher')
            finally:
                os.set_handle_inheritable(stdout,False);os.set_handle_inheritable(stdin,False)
            _ok(k.AssignProcessToJobObject(job,proc.process),'Assign owned launcher before first instruction');assigned=True
            if k.ResumeThread(proc.thread)==0xffffffff:raise OSError(c.get_last_error(),'Resume owned launcher')
            wait=k.WaitForSingleObject(proc.process,int(timeout_seconds*1000))
            if wait not in (0,258):raise OSError(c.get_last_error(),'Wait owned launcher')
            timed_out=wait==258;before=_active(job)
            # Terminate every member while the launcher handle is still held.
            _ok(k.TerminateJobObject(job,124 if timed_out else 0),'Terminate owned process tree')
            deadline=time.monotonic()+10
            while _active(job):
                if time.monotonic()>deadline:raise RuntimeError('Owned job still has active descendants after termination')
                time.sleep(.01)
            code=w.DWORD();_ok(k.GetExitCodeProcess(proc.process,c.byref(code)),'Owned process exit status')
            log.flush();os.fsync(log.fileno())
            return {'exit_code':code.value,'timed_out':timed_out,'launcher_pid':proc.pid,
                    'active_processes_before_cleanup':before,'active_processes_after_cleanup':0,
                    'assigned_before_resume':True,'kill_on_job_close':True,'timeout_seconds':timeout_seconds}
    finally:
        if proc.process and not assigned:k.TerminateProcess(proc.process,125) # Still suspended; no child can exist.
        k.CloseHandle(job) # KILL_ON_JOB_CLOSE also covers Python exceptions/cancellation.
        if proc.thread:k.CloseHandle(proc.thread)
        if proc.process:k.CloseHandle(proc.process)
