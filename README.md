
# ios 用python实现自动打包的方式方式v1
## 先简单说一下我实现的思路一期的思路
	这个脚本自动打包的方式，是根据我自己手动打包的流程来实现的,先在开发证账号下载好需要的证书和描述文件，放到钥匙串里面和xcode 里面，然后配置项目，开始打包
    * 在工程同级目录下面我创建了一个.package 文件，将项目打包需要的资源都放在这个文件下面，项目需要，
        *打包证书，
        * 描述文件，
        * 项目配置文件（configuration这里面我只放了证书密码和项目名称），
        * 还有打包脚本，
    当打包脚本触发的时候会相应的读取项目配置文件，读取密码，然后把证书文件导入钥匙串中，之后会读取描述文件解析文件内容，把需要的描述文件uuid 名称，TeamName，TeamIdentifier，Name解析出来，然后把描述文件复制到Provisioning Profiles文件下面，用uuid起名，前期准备工作就准备完成了，之后就是把描述文件和证书配置到项目中去了，这下完成项目配置，这边还有个操作就是配置项目域名，我在项目中配置了一个plist 做了一个参数修改它来修改当前请求环境，之后就是用xcodebuild生成achive文件，生成ipa文件，压缩
## 说一下代码的实现吧 
### 环境
    * 苹果最新系统，需要有xcode 
    * python3  pip3 环境
### 支持库
    * shutil  文件复制操作库
    * mobileprovision   描述文件解析
    * pbxproj   项目工程配置
    * biplist plist 文件解析
    * zipfile  文件打包压缩
### 特别说明
    现在苹果最新的系统需要的权限比较高，所以记得去给终端高一些的权限
### 代码部分
#### 先读取配置文件获取项目名称和证书密码
    `exportOptionsPlist = os.path.join(project_path + "/.package/exportOptions.plist")`
#### 把指定目录下面的证书循环找出来导入钥匙串 security import   
    ` for cert_name in os.listdir(file + "/certificates/certs"):
        if ".p12" in cert_name:
            cert_file = file + "/certificates/certs/" + cert_name
            os.system(
                "security import " + cert_file + " -k " + keychain_path + " -P " + keychain_password + " -T /usr/bin/codesign")
            systemLog("导入证书：" + cert_name)
    `
#### 解析描述文件 获取UUID、TeamName、TeamIdentifier、Name    
    `mp_model = MobileProvisionModel(mobileprovision_file + mobileprovision_name)
        UUID = mp_model['UUID']
        TeamName = mp_model['TeamName']
        TeamIdentifier = mp_model['TeamIdentifier'][0]
        Name = mp_model['Name']
        print(mp_model)
     `
####      把描述文件放到指定文件（这个思路是我看系统的描述文件都是用它的uuid放到文件夹中的 ，看到效果还不错）
     `shutil.copy(mobileprovision_file + "" + mobileprovision_name,
                    os.path.expanduser('~')+r'/Library/MobileDevice/Provisioning Profiles')`
#### 将项目工程配置
     `project = XcodeProject.load(project_path + '/' + project_name + '/' + project_name + '.xcodeproj/project.pbxproj');
    # project.add_code_sign("Apple Distribution: " + TeamName, TeamIdentifier, UUID,
    #                       Name + ".mobileprovision")
    project.add_code_sign("Apple Distribution: " + TeamName, TeamIdentifier, UUID,
                          Name)`
#### 这个地方是我在项目中会配置一个环境plist 对应的请求域名，来自动化配置环境，
    `path = search(project_path, "configuration.plist")
    plist = readPlist(path)
    # plist.save()
    plist['CURRENT_CONFIGURATION'] = project_url`
    
#### 这个地方就是关键打包的了使用的xcodebuild  先 archive  然后打出安装包
    `os.system("xcodebuild  " +
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
              "-exportOptionsPlist " + exportOptionsPlist)`
#### 最后做了一下压缩，因为生产可能产生两个包 一个appstore一个ad—hoc 用于测试 
    ` zip = zipfile.ZipFile(file + '/'+ "dist.zip" , mode="w")
                zip.write(os.path.join(exportPath, cert_name),cert_name )
                zip.close()`


## 补充
    * 证书和描述文件 这个地方可以扩展变得灵活一些就是用git下载，每次都更新描述文件和证书，这样如果需要更新描述文件了，就可以放到相应的仓库去下载，得到的包就是最新的，不用提交代码，和代码分割开
    * 网上还有一些直接把设备信息写入描述文件的，
    * 还有直接上传到操作，这个氮素写的一个工程上传sftp服务器上面，没有结合，后期添加，并且分渠道上传的功能（fir，蒲公英，appstore等功能）
## info
    这个是我第一次自己这么正经的写一套自己实现的方法吧，希望能给大家带来帮助，如果有问题，或者好的想法，可以一起讨论
    以后如果有时间我还是会升级这个库的，希望能完善咱们ios的打包流程，让我们更自动化
    
    

	
