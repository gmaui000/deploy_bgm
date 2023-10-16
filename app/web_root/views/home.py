#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------

from settings import settings
from flask import Blueprint, render_template, current_app, send_from_directory, request, jsonify
from werkzeug.utils import secure_filename
import os
import time
import hashlib
import json
import glob,shutil

home = Blueprint('home', __name__)


def calc_md5(file):
    with open(file, 'rb') as f:
        h = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            h.update(chunk)
            chunk = f.read(8192)
        return h.hexdigest()


class DocumentReader:

    def __init__(self, real_path):
        self.real_path = real_path

    def analysis_dir(self):
        dirs = []
        files = []
        os.chdir(self.real_path)
        for name in sorted(os.listdir('.'), key=lambda x: x.lower()):
            _time = time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(os.path.getctime(name)))
            if os.path.isdir(name):
                dirs.append([name, _time, '文件夹', '-'])
            elif os.path.isfile(name):
                file_type = os.path.splitext(name)[1]
                size = self.get_size(os.path.getsize(name))
                files.append([name, _time, file_type, size])
        return dirs, files

    @staticmethod
    def get_size(size):
        if size < 1024:
            return '%d  B' % size
        elif 1024 <= size < 1024 * 1024:
            return '%.2f KB' % (size / 1024)
        elif 1024 * 1024 <= size < 1024 * 1024 * 1024:
            return '%.2f MB' % (size / (1024 * 1024))
        else:
            return '%.2f GB' % (size / (1024 * 1024 * 1024))


@home.route('/index')
@home.route('/index/<path:path_uri>')
def index(path_uri=''):
    base_dir = settings.BASEDIR
    real_path = os.path.join(base_dir, path_uri).replace('\\', '/')

    if not os.path.exists(real_path):
        html = render_template('error_404.html')
    else:
        file_reader = DocumentReader(real_path)
        dirs, files = file_reader.analysis_dir()
        html = render_template('index.html',
                               app_name=settings.APPLICATION_NAME,
                               path=path_uri,
                               dirs=dirs,
                               files=files,
                               error_info=None
                               )
    return html


@home.route('/getMusicList', methods=["POST"])
def get_music_list():
    car_type = request.form.get('car_type')
    car_number = request.form.get('car_number')
    base_dir = settings.BASEDIR
    music_dir_list = [
        f'bgm/{car_type}/{car_number}',
        f'bgm/{car_type}/default',
        f'bgm/default'
    ]
    bgms = []
    rel_path = ''
    for i in music_dir_list:
        music_dir = os.path.join(base_dir, i)
        if not os.path.exists(music_dir):
            continue
        bgms = glob.glob(f'{music_dir}/*.mp3')
        if len(bgms) > 0:
            rel_path = i
            break
    fileinfo = []
    for i in bgms:
        if not os.path.isfile(i):
            continue
        filename = os.path.basename(i)
        fileinfo.append(
            {"name": filename, "url": f'/download/{rel_path}/{filename}', "md5": calc_md5(i)})
    return json.dumps(fileinfo)

@home.route('/getWarningSoundList', methods=["POST"])
def get_warning_sounds():
    base_dir = settings.BASEDIR
    sound_dir = os.path.join(base_dir,'warning-sound')
    sounds = glob.glob(f'{sound_dir}/*.wav')
    fileinfo = []
    for i in sounds:
        if not os.path.isfile(i):
            continue
        filename = os.path.basename(i)
        fileinfo.append(
            {"name": filename, "url": f'/download/warning-sound/{filename}', "md5": calc_md5(i)})
    return json.dumps(fileinfo)


@home.route('/download/<filename>')
@home.route('/download/<path:path>/<filename>')
def download(filename, path=None):
    if not path:
        real_path = settings.BASEDIR
    else:
        real_path = os.path.join(settings.BASEDIR, path)
    return send_from_directory(real_path, filename, mimetype='application/octet-stream')


@home.route('/upload', methods=['GET', 'POST'])
def upload():
    html = ''
    if request.method == 'POST':
        path = request.form.get('upload_path')
        file = request.files['upload_file']
        base_dir = settings.BASEDIR

        if file:
            filename = _get_filename(file)
            save_path = os.path.join(base_dir, path, filename)
            file.save(save_path)
            html = jsonify({"code": 200, "info": "文件：%s 上传成功" % filename})
        else:
            html = jsonify({"code": 201, "info": "未选择文件"})
    else:
        html = jsonify({"code": 201, "info": "禁止使用爬虫上传文件"})
    return html


def _get_filename(file):
    return file.filename
    # secure_filename 可以处理路径穿越等问题，但是会把文件名中中文去掉，故无法使用
    # return secure_filename(file.filename)


@home.errorhandler(500)
def error(error):
    return render_template('error_500.html')


@home.route('/createdir/<dirname>',methods=['POST'])
@home.route('/createdir/<path:path>/<dirname>',methods=['POST'])
def create_dir(dirname, path=None):
    if not path:
        real_path = settings.BASEDIR
    else:
        real_path = os.path.join(settings.BASEDIR, path)
    fullpath = os.path.join(real_path,dirname)
    if os.path.exists(fullpath):
        return jsonify({"code":304,"info":"目录已经存在"})
    try:
        os.makedirs(fullpath)
    except:
        return jsonify({"code":500,"info":"创建目录失败"})
    return jsonify({"code":200,"info":"创建目录成功"})


@home.route('/deleteResource/<dirname>',methods=['POST'])
@home.route('/deleteResource/<path:path>/<dirname>',methods=['POST'])
def delete_resource(dirname,path=None):
    if not path:
        real_path = settings.BASEDIR
    else:
        real_path = os.path.join(settings.BASEDIR, path)
    fullpath = os.path.join(real_path,dirname)
    print("fullpath : ",fullpath)
    if not os.path.exists(fullpath):
        return jsonify({"code":304,"info":"目录已经存在"})
    try:
        if os.path.isdir(fullpath):
            shutil.rmtree(fullpath)
        elif os.path.isfile(fullpath):
            os.remove(fullpath)
    except:
        return jsonify({"code":500,"info":f'删除目录{dirname}失败'})
    return jsonify({"code":200,"info":"删除目录成功"})
