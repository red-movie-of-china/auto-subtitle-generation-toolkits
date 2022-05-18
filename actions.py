"""
    JianYing Srt Parser
    For Asdb 
    By @P_P_P_P_P
"""
import pyautogui , time , os , subprocess, json , sys, subprocess , datetime , base64 , pytz, os
import uiautomation as auto
import components.ui as ui
import components.video_Down as vd
from components.preprocess.split_audiobook import split_audiofile
import av
import string
import srt
from pydub import AudioSegment
from pypinyin import pinyin, lazy_pinyin
from components.preprocess.audio_split import split_to_clips_in_minutes

Start_Time = time.time()
Config = json.loads(open("./Config.json","r",encoding="utf-8").read())

def Start_Func(func):
    def deco(*args, **kwargs):
        os.system('echo Function: {_funcname_}'.format(_funcname_=func.__name__))
        start_time = time.time()
        res = func(*args, **kwargs)
        os.system('echo Function :{_funcname_} Finished in  {_time_} Sec'
              .format(_funcname_=func.__name__, _time_=(time.time() - start_time)))
        return res
    return deco



class Etcs:
    def Screenshot(self,delay:int):
        while True:
            time.sleep(delay)
            pyautogui.screenshot(f"{Config['Sources_Path']}{int(time.time()-Start_Time)}.png")
    
    @Start_Func
    def Get_Paths(self):
        whoami = os.popen("whoami").read().replace("\n","").split("\\")[0]
        print(whoami)
        # [1]
        Base_Dir = "C:/Users/{}/AppData/Local/JianyingPro".format(whoami)
        Config["Base_Dir"] ,Config["JianYing_App_Path"]  = Base_Dir , '/'.join([Base_Dir,"Apps/JianyingPro.exe"])

    def Kill_All(self):
        subprocess.Popen('%s%s' % ("taskkill /F /T /IM ","VEDetector.exe"),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).wait()
        subprocess.Popen('%s%s' % ("taskkill /F /T /IM ","JianYingPro.exe"),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).wait()
        return 

    def Start_JianYing(self):
        return subprocess.Popen(Config["JianYing_App_Path"],shell=True)

class Actions:

    @Start_Func
    def Install_JianYing(self):
        os.mkdir("./components/tmp") if not os.path.exists("./components/tmp") else None
        #subprocess.run("choco install -y ffmpeg aria2 7zip",shell=False
        #    ,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.Popen(f"aria2c  -x 16 -s 16 -k 1M -o ./_tmp.exe {Config['Jy_Download_Url']}",shell=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).wait()
        os.system(f"echo Finish Install Dependiencies")
        install_process = subprocess.Popen("_tmp.exe",shell=True)
        while True:
            if auto.WindowControl(searchDepth=1,ClassName="#32770").Exists(): break
        Instance = auto.WindowControl(searchDepth=1,ClassName="#32770")
        auto.Click(x=Instance.BoundingRectangle.xcenter(),y=int(Instance.BoundingRectangle.ycenter()-Instance.BoundingRectangle.height()/8))
        while True:
            if os.path.exists(Config["JianYing_App_Path"]): break
        install_process.kill()
        Etcs().Kill_All()
        while auto.WindowControl(searchDepth=1,ClassName="#32770").Exists(): auto.Click(x=Instance.BoundingRectangle.xcenter(),y=int(Instance.BoundingRectangle.ycenter()-Instance.BoundingRectangle.height()/8))


    @Start_Func
    def Took_Draft_Content_Path(self):
        Etcs().Kill_All()
        Jian_Ying_Process = Etcs().Start_JianYing()
        while ui.Locate_Status(timeout_seconds=2) != 0:...
        before_list = os.listdir(Config["Base_Dir"]+"/User Data/Projects/com.lveditor.draft")
        jy_window = auto.WindowControl(Name="JianyingPro",searchDepth=1)
        jy_window.SetTopmost()
        jy_window.TextControl(Name="HomePageStartProjectName",searchDepth=1).Click()
        while ui.Locate_Status(timeout_seconds=2) != 1:...
        Jian_Ying_Process.kill()
        Etcs().Kill_All()
        after_list = os.listdir(Config["Base_Dir"]+"/User Data/Projects/com.lveditor.draft")
        Config["Draft_Content_Json"] = Config["Base_Dir"] + "/User Data/Projects/com.lveditor.draft/" +  [i for i in after_list if i not in before_list][0] + "/draft_content.json"

class Release:


    Release_Introduce = ""
    def Create_Assets(self):
        os.system("7z a -tzip {}All.zip {}*.srt {}*.png {}*.jpg".format(Config["Sources_Path"],Config["Sources_Path"],Config["Sources_Path"],Config["Sources_Path"]))

    def Output_Version(self):
        env_file = os.getenv('GITHUB_ENV')
        tz = pytz.timezone('Asia/Shanghai')
        date = datetime.datetime.now(tz).strftime("%Y.%m.%d_%H/%M")
        tags = base64.encodebytes(self.Release_Introduce.encode('utf-8')).decode('utf-8').replace('\n','') + date
        os.system(f"echo Introduce : {self.Release_Introduce} , date:{date} , tags:{tags}")
        with open(env_file, "a") as f:
            f.write(f"Version=1.0")
            f.write("\n")
            f.write(f"Tags={tags}")
            f.write("\n")
            f.write(f"Introduce={self.Release_Introduce}")
        os.system(f"echo env: {env_file}")


def format_filename(s):
    """Take a string and return a valid filename constructed from the string.
Uses a whitelist approach: any characters not present in valid_chars are
removed. Also spaces are replaced with underscores.
 
Note: this method may produce invalid filenames such as ``, `.` or `..`
When I use this method I prepend a date string like '2009_01_15_19_46_32_'
and append a file extension like '.txt', so I avoid the potential of using
an invalid filename.
 
"""


    # os.rename(s, '-'.join(lazy_pinyin(s)))
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename=''
    for c in s:
        if not c in valid_chars:
            c=''.join(lazy_pinyin(c))
        filename=filename+c
    # filename = ''.join( lazy_pinyin(c) for c in s if not c in valid_chars)
    filename = filename.replace(' ','_') # I don't like spaces in filenames.
    return filename

def videopreprocess(dir):
    print('original video dir',dir)
    if not dir.endswith(os.sep):
        dir=dir+os.sep
    from os.path import isfile, join
#create video dir for each video
    basepath = os.path.abspath(dir)
    print('original video dir abs path',basepath)
    onlydirs=[]

    media_list = [fn for fn in os.listdir(basepath) if any(fn.endswith(format) for format in ['.mp4','.avi','.mkv','.mov','.flv'])]
    if len(media_list)>0:
        for f in media_list:
            name=f.split('.')[0]
            ext=f.split('.')[-1]
            newvideoname=format_filename(name)
            os.rename(join(basepath,f), join(basepath,newvideoname+'.'+ext)) 
            print('format filename done',newvideoname)

            name=newvideoname
            audiopath=join(basepath,newvideoname+'.aac')

            videopath=basepath+os.sep+newvideoname+'.'+ext
            os.system(f"echo Start convert video to audio only {name}")
            # start = time.time()
            # stop = time.time()
            if not os.path.exists(audiopath):
                isdone=subprocess.Popen(f'ffmpeg -y -i "{videopath}" -vn -codec copy "{audiopath}"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, err = isdone.communicate()

                if isdone.returncode == 0 and os.path.exists(join(basepath,newvideoname+'.aac')):
                    print("video to audio Job done.")
                else:
                    print("video to audio ERROR",err)
                    print(out)    
            else:
                print('video audio file is here',audiopath)
            os.system(f"echo Start split >120 minutes audio to parts {audiopath}")

            # split_to_clips_in_minutes(join(basepath,name+'.aac'),duration=60)

            # ffmpeg -i sourcefile.aac -f segment -segment_time 4 -c copy out/%03d.aac
            if os.path.exists(audiopath):
                print('start split audio into 60 minutes clip',audiopath)
                if not os.path.exists(basepath+os.sep+name):
                    print('making new video dir for this video',basepath+os.sep+name)
                    os.mkdir(basepath+os.sep+name)
                print(f'ffmpeg -y -i "{audiopath}"  -f segment -segment_time 3600 -c copy "{basepath+os.sep+name}"/%01d.aac')

                isdone= subprocess.Popen(f'ffmpeg -y -i "{audiopath}"  -f segment -segment_time 3600 -c copy "{basepath+os.sep+name}"/%01d.aac',shell=True,
                stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
                out, err = isdone.communicate()

                if isdone.returncode == 0 and os.path.exists(join(basepath,newvideoname+'.aac')):
                    print("split Job done.")
                else:
                    print("split Job ERROR",err)
                    print(out)    


                # split_audiofile(join(basepath,name+'.aac'),l=3600,remove=False)
                onlydirs = [join(basepath,f) for f in os.listdir(basepath) if not isfile(join(basepath, f))]
    return onlydirs
# iterate video dir,convert original video to audio, detect audio length >120 minutes,cut ,remove original audio


if __name__ == "__main__":
    Running_Type = sys.argv[1] if len(sys.argv) > 1 else "local"

    if Running_Type == "local":
        Etcs().Get_Paths()
        videodirs=videopreprocess(Config['Sources_Path'])
        if len(videodirs)>0:
            Config["JianYing_App_Path"]=r'D:\Program Files (x86)\JianyingPro\JianyingPro.exe'
            Actions().Took_Draft_Content_Path()
            ui.CONFIG["draft_content_directory"] = Config["Draft_Content_Json"]
            ui.CONFIG["JianYing_Exe_Path"] = Config["JianYing_App_Path"]
            # preprocess video
            for dir in videodirs:
                start = time.time()
                basepath = os.path.abspath(Config['Sources_Path'])
                srtname=dir.split(os.sep)[-1]+'.srt'
                if not os.path.exists(basepath+os.sep+srtname):
                
                    ui.Multi_Video_Process(video_path=dir)
                    stop = time.time()
                    print('===convert srt time cost=====',stop-start)

                    # combine srt into whole
                    srt_list = [fn for fn in os.listdir(dir) if any(fn.endswith(format) for format in ['.srt'])]
                    final_subtitle=[]
                    td_to_shift  = datetime.timedelta(seconds=0)
                    # offset  = datetime.timedelta(seconds=0)
                    # total  = datetime.timedelta(seconds=0)
                    total=0
                    
                    for i in range(len(srt_list)):
                        try:
                            with open(dir+os.sep+str(i)+'.srt',encoding='utf-8') as f:
                                subtitles=list(srt.parse(f.read()))
                                stream=av.open(dir+os.sep+str(i)+'.aac').streams.audio[0]
                                duration=stream.duration/stream.time_base
                                duration=AudioSegment.from_file(dir+os.sep+str(i)+'.aac').duration_seconds
                                # seconds_to_shift=6000
                                print('audio length',duration)
                                td_to_shift = datetime.timedelta(seconds=(total))
                                # try to use srt to compute offset ,but srt length is not audio file length at all
                                # if subtitles[-1].end>datetime.timedelta(seconds=3600):
                                #     offset=subtitles[-1].end-datetime.timedelta(seconds=3600)
                                #     total=total+offset

                                # else:
                                #     # offset=datetime.timedelta(seconds=0)
                                    
                                #     offset=(datetime.timedelta(seconds=3600)-subtitles[-1].end)
                                #     print('---------',total)
                                #     print('=========',offset)
                                #     total=total-offset

                                print('i==',i,' 本字幕应偏移时间 ',td_to_shift,'本次偏移值',duration,'累计与标准偏移的差值',total)

                                for subtitle in subtitles:
                                    subtitle.start += td_to_shift
                                    subtitle.end += td_to_shift
                                    final_subtitle.append(subtitle)
                                
                                total=total+duration

                        except srt.SRTParseError:
                            print('invalid srt found',i,' in this dir: ',dir)
                    

                    print('final srt ',basepath+os.sep+srtname)
                    with open(basepath+os.sep+srtname, 'w', encoding='utf-8') as f:  f.write(srt.compose(final_subtitle))
                    


    elif Running_Type == "actions":
        from threading import Thread
        # Run on Github
        r = Release()
        Thread(target=Etcs().Screenshot,args=(1,),daemon=True).start()

        Etcs().Get_Paths()
        Actions().Install_JianYing()
        Actions().Took_Draft_Content_Path()
        ui.CONFIG["draft_content_directory"] = Config["Draft_Content_Json"]
        ui.CONFIG["JianYing_Exe_Path"] = Config["JianYing_App_Path"]
    
        for item in Config["url"]:
            r.Release_Introduce += item+";"
            vd.yt_dlp(item)
            # if "bv" in item.lower() or "bilibili.com" in item.lower(): vd.bilibili(item,ASDB=Config["ASDB"],download_sourcer=0)
            # else: vd.aria2(item,item.split("/")[-1])
        # 每个视频一个文件夹

        try:
            ui.Multi_Video_Process(video_path=Config['Sources_Path'])
        except Exception as e:
            if not Config["DEBUG"]:  raise e
        r.Create_Assets(),r.Output_Version()

    elif Running_Type == "install": Actions().Install_JianYing()
    elif Running_Type == "nonactions":
        Etcs().Get_Paths()
        Actions().Took_Draft_Content_Path()
        ui.CONFIG["draft_content_directory"] = Config["Draft_Content_Json"]
        ui.CONFIG["JianYing_Exe_Path"] = Config["JianYing_App_Path"]
        for item in Config["url"]:
            # if "bv" in item.lower() or "bilibili.com" in item.lower(): vd.bilibili(item,ASDB=Config["ASDB"],download_sourcer=0)
            # else: vd.aria2(item,item.split("/")[-1])
            vd.yt_dlp(item)

        ui.Multi_Video_Process(video_path=Config['Sources_Path'])
