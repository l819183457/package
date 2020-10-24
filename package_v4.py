#!/usr/bin/python
# -*- coding: UTF-8 -*-



"""
环境
    * 苹果最新系统
    * python3  pip3 环境
构建流程
    * 输入构建环境
    * 获取项目配置文件 configuration
        * 项目id
        * 证书密码
        * 项目名称
    * 获取证书  导入钥匙串中  这里需要上一步的密码
    * 获取描述文件解析
        * uuid （文件名称）
        * TeamName ***** Information Service Co.,Ltd.
        * TeamIdentifier  BSNMQ3E4FW
        * Name  com.ehking.pro.gonggong_06
    * 配置环境需要的参数
    * 生成 achive 文件
    * 生成api
    * 压缩文件
"""


import os, time
import sys
try:
   import shutil
except ImportError:
  os.system('pip3 install shutil')
  import shutil

try:
   from mobileprovision import MobileProvisionModel
except ImportError:
  os.system('pip3 install PyMobileProvision')
  from mobileprovision import MobileProvisionModel
try:
   from pbxproj import XcodeProject
except ImportError:
  os.system('pip3 install pbxproj')
  from pbxproj import XcodeProject

try:
   from biplist import *
except ImportError:
  os.system('pip3 install biplist')
  from biplist import *

try:
   import zipfile
except ImportError:
  os.system('pip3 install zipfile')
  import zipfile

project_url = "90004"
keychain_path = '~/Library/Keychains/login.keychain'

UUID = ''
TeamName = ''
TeamIdentifier = ''
Name = ''

def start():
    global project_url
    global project_path

    project_url = sys.argv[1]
    project_path = os.path.abspath(os.path.join(os.getcwd(), "..")) #os.getcwd()

    systemLog("初始化 构建容器")
    file = os.path.join(project_path + "/.package")
    # 获取项目的名称和证书的密码
    exportOptionsPlist = os.path.join(project_path + "/.package/exportOptions.plist")
    if not (os.path.exists(file)  and os.path.exists(exportOptionsPlist)):
        systemLog("文件不存在，请检查代码")
        # return
    info = readPlist(project_path + "/.package/" + "configuration.plist")
    project_name = info["project_name"]
    keychain_password = info['keychain_password'] 
    project_id = info['project_id']
    #  读取文件 导入证书描述文件配置
    systemLog("开始导入证书")
    for cert_name in os.listdir(file + "/certificates/certs"):
        if ".p12" in cert_name:
            cert_file = file + "/certificates/certs/" + cert_name
            os.system(
                "security import " + cert_file + " -k " + keychain_path + " -P " + keychain_password + " -T /usr/bin/codesign")
            systemLog("导入证书：" + cert_name)
    systemLog("导入证书完成")
    # 描述文件解析 -
    systemLog("描述文件解析")
    global UUID
    global TeamName
    global TeamIdentifier
    global Name

    mobileprovision_file = project_path + '/.package/certificates/profiles/AdHoc/'
    if project_url == "90004" :
        mobileprovision_file = project_path + '/.package/certificates/profiles/Appstore/'
    else:
        mobileprovision_file = project_path + '/.package/certificates/profiles/AdHoc/'


    for mobileprovision_name in get_mobileprovision_files(mobileprovision_file):
       # print(os.path.expanduser('~'))

        shutil.copy(mobileprovision_file + "" + mobileprovision_name,
                    os.path.expanduser('~')+r'/Library/MobileDevice/Provisioning Profiles')
        mp_model = MobileProvisionModel(mobileprovision_file + mobileprovision_name)
        UUID = mp_model['UUID']
        TeamName = mp_model['TeamName']
        TeamIdentifier = mp_model['TeamIdentifier'][0]
        Name = mp_model['Name']
        print(mp_model)
    systemLog("描述文件解析完成")
    # 项目配置
    systemLog("项目配置（描述文件，证书，账号信息）")
    project = XcodeProject.load(project_path + '/' + project_name + '/' + project_name + '.xcodeproj/project.pbxproj');
    # project.add_code_sign("Apple Distribution: " + TeamName, TeamIdentifier, UUID,
    #                       Name + ".mobileprovision")
    project.add_code_sign("Apple Distribution: " + TeamName, TeamIdentifier, UUID,
                          Name)
    project.save()
    systemLog("项目配置完成")
    #
    #
    systemLog("项目环境配置")
    path = search(project_path, "configuration.plist")
    plist = readPlist(path)
    # plist.save()
    plist['CURRENT_CONFIGURATION'] = project_url
    writePlist(plist, path)
    print(path)
    systemLog("项目环境配置完成")
    systemLog("项目构建开始（FastLane）")
    # 格式化成2016-03-20 11:45:39形式

    op = "hoc_" + time.strftime("%Y%m%d-%H%M%S", time.localtime())
    if project_url == "90004" :
        op = "hoc_" + time.strftime("%Y%m%d-%H%M%S", time.localtime())
    else:
        op = "appleStore_" + time.strftime("%Y%m%d-%H%M%S", time.localtime())
    archivePath = project_path + "/.package/build/archive/" + op + ".xcarchive"


    # 安装包
    os.system("xcodebuild  " +
              "-workspace " + project_path + '/' + project_name + '/' + project_name + ".xcworkspace " +
              "-scheme " + project_name + " " +
              "-configuration Release " +
              "-destination generic/platform=iOS " +
              "-archivePath " + archivePath + " " +
              "clean " +
              "archive")
    plist = readPlist(exportOptionsPlist)
    plist["provisioningProfiles"][project_id] = Name
    writePlist(plist, exportOptionsPlist)
    exportPath = project_path + '/.package/build/' + op
    os.system("xcodebuild " +
              "-exportArchive " +
              "-archivePath " + archivePath + " "
              "-exportPath " + exportPath + " "
              "-exportOptionsPlist " + exportOptionsPlist)


    #  压缩
    if os.path.exists(exportPath):
        for cert_name in os.listdir(exportPath):
            if ".ipa" in cert_name:
                zip = zipfile.ZipFile(file + '/'+ "dist.zip" , mode="w")
                zip.write(os.path.join(exportPath, cert_name),cert_name )
                zip.close()




def systemLog(msg):
    print('\033[5;35m======================|  ' + msg +'  |=====================\033[0m')


def get_mobileprovision_files(path):
    for f in os.listdir(path):
        if f.endswith('.mobileprovision'):
            yield f


def search(path,name):
    for root, dirs, files in os.walk(path):  # path 为根目录
        if name in dirs or name in files:
            flag = 1      #判断是否找到文件
            root = str(root)
            dirs = str(name)
            return os.path.join(root, name)
    return -1


def get_path(path_int):
    '''
    :param path_int: 0表示获取当前路径，1表示当前路径的上一次路径，2表示当前路径的上2次路径，以此类推
    :return: 返回我们需要的绝对路径，是双斜号的绝对路径
    '''
    path_count=path_int
    path_current=os.path.abspath(r".")
    # print('path_current=',path_current)
    path_current_split=path_current.split('\\')
    # print('path_current_split=',path_current_split)
    path_want=path_current_split[0]
    for i in range(len(path_current_split)-1-path_count):
        j=i+1
        path_want=path_want+'\\\\'+path_current_split[j]
    return path_want


if __name__ == "__main__":

    start()


"""
    * 分成dev  qa uat  qa 的脚本
    * 然后一起使用build.js 运行
    * 将生成的 api 打包放入文件dist里面
    


"""
#  WENTI
"""
    * python3 环境需要sudo 权限
    * 获取文件的时候小找我要权限
    * 第一次取证书时候需要授权才能取到



"""

