# coding = gbk
import contextlib
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import winsound

ffmpeg_state = 2  # ffmpeg 是否可用 1可 0不可 2不确定


# 创建文件夹
def mkdir(path):
    import os
    path = path.strip()
    path = path.rstrip("\\")
    if isExists := os.path.exists(path):
        # print(' 创建过了')
        return False
    os.makedirs(path)
    print(f'\n{path} 创建成功\n')
    return True


def set_thread():
    while 1:
        thread = input('下载线程 (推荐为2或者直接回车) :')
        if len(thread) == 0:
            thread = 2
            break
        else:
            try:
                thread = int(thread)
                break
            except ValueError:
                print('请确保输入的是数字！！！\n')
    return thread


def get_m3u8(workdir):
    m3u8_path = []
    m3u8_name = []
    file_or_dir = ''
    if os.path.isdir(workdir):
        file_or_dir = 'dir'
        files = os.listdir(workdir)
        for file in files:
            if file.find('.m3u8') != -1:
                m3u8_name.append(file)
                file = os.path.join(workdir, file)
                # print(file)
                m3u8_path.append(file)
    elif workdir.find('.m3u8') != -1:
        file_or_dir = 'file'
        m3u8_path.append(workdir)
        m3u8_name.append(workdir.split('\\')[-1])
    if not m3u8_path:
        print(f'{workdir}内没有找到m3u8文件')
        m3u8_path = False
    return m3u8_path, m3u8_name, file_or_dir


def run_cmd_Popen_PIPE(cmd_string, file):
    import subprocess
    # print('运行cmd指令：{}'.format(cmd_string))
    print(f'ffmpeg合并 {file} 中。。。\t\t可能会耗时比较长')
    return \
        subprocess.Popen(cmd_string, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         encoding='utf-8').communicate()[0]


def thread_ffmpeg(mp4_path):
    cmd = fr'ffmpeg -hide_banner -y -i "{mp4_path}.mp4" -c:v copy -c:a copy "{mp4_path}_new.mp4"'
    run_cmd_Popen_PIPE(cmd, mp4_path)
    os.remove(f'{mp4_path}.mp4')
    os.rename(f'{mp4_path}_new.mp4', f'{mp4_path}.mp4')


def cmd_rum(first_download_path):
    os.system(f"copy /b {first_download_path}\\*.ts {first_download_path}.mp4")  # 合并
    os.system('cls')
    shutil.rmtree(first_download_path)


def ffmpeg_run(workdir):
    global ffmpeg_state
    if ffmpeg_state != 1:  # 不确定是否可用的状态
        state = os.system('ffmpeg -version')
        os.system('cls')
        if state == 0:
            ffmpeg_state = 1
        else:
            print('此设备未下载ffmpeg或者未放入系统变量，将默认使用二进制合并\n')
            ffmpeg_state = 0
    if ffmpeg_state == 1:
        dirs = os.listdir(workdir)
        with ThreadPoolExecutor(3) as f:
            for i in dirs:
                if i.find('.mp4') != -1:
                    i = i.replace('.mp4', '')
                    mp4_path = os.path.join(workdir, i)
                    f.submit(thread_ffmpeg, mp4_path)


def get_m3u8_link_download(m3u8_path, m3u8_name, first_download_path):  # 一集
    all_index = 0
    m3u8_links = []
    with open(m3u8_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.find('#EXT') == -1:
                m3u8_links.append(line)
                all_index += 1
    if not m3u8_links:
        print(f'{m3u8_name}文件内未找到链接')
        return
    else:
        print(f'\n下载 {m3u8_name} 中。。。。\n', end='')
        mkdir(first_download_path)
        with ThreadPoolExecutor(16) as f:
            for link, i in zip(m3u8_links, range(len(m3u8_links))):
                f.submit(m3u8_download, link, first_download_path, i, len(m3u8_links))
        # for link, i in zip(m3u8_links, range(len(m3u8_links))):
        #     first_download_path = workdir + '\\' + m3u8_name.replace('.m3u8', '')  # workdir\间谍过家家第1集\
        #     mkdir(first_download_path)
        #     m3u8_download(link, first_download_path, i, len(m3u8_links))

        # print("转换为mp4 完成")


def m3u8_download(url, name, i, all_i):
    # global count
    while len(str(i)) < 4:
        i = f'0{str(i)}'
    file_name = f'{name}\\{i}.ts'  # workdir\间谍过家家第1集\0001.ts
    head = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
    while 1:
        with contextlib.suppress(requests.exceptions.RequestException):
            resp = requests.get(url, timeout=5, headers=head).content[212:]
            with open(file_name, 'wb') as f:
                f.write(resp)
            i = int(i)
            if i % 5 == 0:
                percent_i = f'{str(round(((i / all_i) * 100), 2))}%'
                print(f'{name} 进度为 {i}/{all_i} {percent_i}\r', end='')
            break


def main(workdir, thread):  # m3u8目录类似 D:\桌面\夏日重现    线程数
    workdir = workdir.replace('/', '\\').strip()
    get_m3u8s = get_m3u8(workdir)
    m3u8_paths, m3u8_names, file_or_dir = get_m3u8s[0], get_m3u8s[1], get_m3u8s[2]
    if m3u8_paths:
        if file_or_dir == 'file':
            workdir = '\\'.join(workdir.split('\\')[:-1])
        first_download_path_list = []
        with ThreadPoolExecutor(thread) as f:
            for m3u8_path, m3u8_name in zip(m3u8_paths, m3u8_names):
                first_download_path = workdir + '\\' + m3u8_name.replace('.m3u8', '')  # workdir\间谍过家家第1集\
                if first_download_path.find(' ') == -1:
                    f.submit(get_m3u8_link_download, m3u8_path, m3u8_name, first_download_path)
                    first_download_path_list.append(first_download_path)
                else:
                    print('\n发现路径内有空格！！！请删除后再运行!')
                    return
        # for m3u8_path, m3u8_name in zip(m3u8_paths, m3u8_names):
        #     get_m3u8_link_download(m3u8_path, m3u8_name)
        for first_download_path in first_download_path_list:  # cmd 合并
            cmd_rum(first_download_path)
        for path in m3u8_paths:  # 删除m3u8文件
            os.remove(path)
        if ffmpeg_state != 0:  # ffmpeg 合并
            ffmpeg_run(workdir)
        print('操作完成！！！')


def user_use():
    while 1:
        workdir = input('\n----请输入或拖拽 存有m3u8的文件夹 或 m3u8单文件----\t\t注意路径不能有空格！！！\n').replace('"', '').replace('"', '')
        thread = set_thread()
        main(workdir, thread)
        winsound.MessageBeep(100)


if __name__ == '__main__':
    """
    文件路径操作
    workdir(即存放m3u8的文件夹) = D:\\桌面\\夏日重现
    m3u8片段下载 D:\\桌面\\夏日重现\\夏日重现第1集\\0001.ts
    
    单文件
    file = D:\\桌面\\夏日重现第1集.m3u8
    workdir = D:\\桌面
    m3u8片段下载 D:\\桌面\\夏日重现第1集\\0001.ts
    """
    user_use()
