#!/usr/bin/python

import asyncio
import argparse
from subprocess import Popen, PIPE
from time import gmtime, strftime
from sys import stderr, exit
from os import path, mkdir
from typing import List, Tuple, Union, Literal

def get_file_length(filename: str) -> Union[float, Literal[False]]:
    fileend: Union[float, Literal[False]] = False
    try:
        info = Popen(["mediainfo", "--Output=Audio;%Duration%", filename],
                stdout=PIPE)
        if info.wait() == 0 and info.stdout is not None:
            lenstring = info.stdout.read().strip()
            if lenstring.isdigit():
                fileend = int(lenstring)/1000

    except FileNotFoundError:
        error_print("mediainfo not found", "warning")
        # if end is None:
        error_print("end time must be supplied", "error")

    return fileend

def format_time(sec) -> str:
    return strftime("%H:%M:%S", gmtime(sec))

def parse_time(time: str) -> int:
    hhmmss: List[str] = time.strip().split(":")
    if len(hhmmss) != 3:
        error_print(f'badly formatted time "{time}"', "error")
        return False

    try:
        hours = int(hhmmss[0])
        minutes = int(hhmmss[1])
        seconds = int(hhmmss[2])
    except:
        return False

    if minutes > 59 or seconds > 59:
        return False

    return hours * 3600 + minutes * 60 + seconds

def error_print(msg: str, level: str):
    print(f"{level}: {msg}", file=stderr)


def split_to_clips_in_minutes(filename,speedup=1.0,start=None,end=None,outputdir=None,threads=4,prefix='',numbering_start=0,dry_run=False,duration=20,audioformat='aac',):

    parser = argparse.ArgumentParser(description="Split up an audio file into "
            "multiple shorter files.")

    parser.add_argument("filename", metavar="FILE")
    parser.add_argument("-s", "--start", metavar="HH:MM:SS",
            help="the starting position of the first part (defaults to 00:00:00)")
    parser.add_argument("-e", "--end", metavar="HH:MM:SS",
            help="the ending position of the last part (defaults to "
            "the end of the track)")
    parser.add_argument("--speedup", type=float, default=1.0, metavar="<float>",
            help="speed up factor (defaults to 1.0)")
    parser.add_argument("-d", "--duration", type=float, default=20.0,
            metavar="<float>",
            help="length of an individual part in minutes (defaults to 20)")
    parser.add_argument("-o", "--outputdir", help="the directory to output "
            "the newly split parts (defaults to the working directory)")
    parser.add_argument("-f", "--audioformat", metavar="<filetype>", default="ogg",
            help="the audio format to use for output (defaults to ogg)")
    parser.add_argument("-p", "--prefix", help="the prefix part of new files' "
            "names (defaults to the original file's name)")
    parser.add_argument("-n", "--numbering-start", type=int, default=1,
            metavar="<integer>", help="the position to start the new files'"
            "numbering from (defaults to 1)")
    parser.add_argument("-t", "--threads", type=int, default=2, metavar="<integer>",
            help="the number of worker threads to spawn (defaults to 2)")
    parser.add_argument("--dry-run", action="store_const",
            const=True, default=False, help="show the new files that would be "
            "created if run without this flag")


    # args = parser.parse_args()

    if not path.isfile(filename):
        error_print(f'file not found "{filename}"', "error")
        exit(1)

    if not start is None:
        start = parse_time(start)
        if not start:
            error_print('invalid start time', 'error')
            exit(1)
    else:
        start = 0

    if not end is None:
        end = parse_time(end) * 1.0
        if not end:
            error_print('invalid end time', 'error');
            exit(1)
    else:
        print('///',filename)
        end = get_file_length(filename)

    if speedup <= 0:
        error_print("speedup factor must be greater than zero", "error")
        exit(1)

    if threads < 1:
        error_print("the number of worker threads must be at least 1", "error")
        exit(1)

    if prefix is None:
        prefix = f"{path.split(path.splitext(filename)[0])[1]}-"
    else:
        prefix = prefix
        if len(prefix) > 0:
            prefix = f"{prefix}-"

    if not outputdir is None:
        outputdir = outputdir
        if not path.isdir(outputdir) and not dry_run:
            mkdir(outputdir)
    else:
        if path.exists(path.split(path.splitext(filename)[0])[1]):
            mkdir(path.split(path.splitext(filename)[0])[1])
        outputdir=path.split(path.splitext(filename)[0])[1]


    part = numbering_start
    duration = duration * 60
    work_queue: asyncio.Queue = asyncio.Queue()
    while (start < end):
        if start + duration < end:
            partend = start + duration
        else:
            partend = end

        outfilename = path.join(outputdir, f"{prefix}{str(part)}.{audioformat}")
        if dry_run:
            print(f"{outfilename} [{format_time(start)}-{format_time(partend)}]")
        else:
            work_queue.put_nowait((filename, start, partend, speedup,
                outfilename))

        start += duration
        part += 1


    async def split_part(filename, start, end, speedup, outfile):
        p = await asyncio.create_subprocess_exec("mpv",
                "--af=scaletempo", "--no-terminal",
                f"--start={format_time(start)}", f"--end={format_time(end)}",
                f"--speed={str(speedup * 1.0)}",
                filename, f"-o={outfile}")

        if (await p.wait()) != 0:
            print(f'Error splitting part starting at {start} \
                    and ending at {end} into {outfile}')

    async def split_dispatcher(queue: asyncio.Queue):
        while True:
            params = await queue.get()
            await split_part(params[0], params[1], params[2], params[3], params[4])
            work_queue.task_done()

    async def worker_dispatcher(threads: int = 2):
        tasks = []
        for i in range(threads):
            task = asyncio.create_task(split_dispatcher(work_queue))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    asyncio.run(worker_dispatcher(threads))
