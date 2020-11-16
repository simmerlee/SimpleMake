# 這是一個python3腳本

import json
import os.path
import argparse
import sys
import shutil
from SimpleMakeConfig import *

SIMPLE_MAKE_VERSION = 'v0.0.1'

def errorExit(msg) :
    print('Error: %s'%(msg))
    exit(1)

# 在l中查找data，找到时返回index，否则返回-1
def list_find(l, data):
    for i in range(0, len(l)):
        if l[i] == data:
            return i
    return -1

# 把l中的第src_idx移动至dst_idx，其他元素相应的也会移动
def list_move(l, src_idx, dst_idx):
    tmp = l[src_idx]
    if src_idx == dst_idx:
        return
    if src_idx > dst_idx:
        for i in range(dst_idx, src_idx):
            l[i+1] = l[i]
    else:
        for i in range(src_idx, dst_idx):
            l[i] = l[i+1]
    l[dst_idx] = tmp

# 把字符串列表l中的字符串拼接成一个字符串并返回
def str_list_to_str(l):
    ret = ''
    for s in l:
        ret += s
    return ret

# 获取文件夹内指定后缀的所有文件
# 返回符合要求的文件的文件全称和不带后缀的名称的列表[(full_name, base_name) ...]
def get_file_by_suffix(dir_name, suffix_set):
    files = os.listdir(dir_name)
    ret = []
    for file_name in files:
        split_name = file_name.split('.')
        if len(split_name) == 0:
            continue
        suffix = split_name[-1]
        base_name = str_list_to_str(file_name.split('.')[:-1])
        is_match = False
        if suffix in suffix_set:
            is_match = True
        if is_match and os.path.isfile(dir_name + '/' + file_name):
            ret.append((file_name, base_name))
    return ret    

# 执行shell命令
# 成功时无返回值，失败时打印错误信息并退出
def printAndExecuteCmdStr(cmd_str, err_msg):
    print('    ' + cmd_str)
    ret = os.popen(cmd_str)
    ret.read()
    ret_code = ret.close()
    if ret_code != None:
        errorExit(err_msg)

if __name__ == '__main__':
    # 检查命令行参数
    ap = argparse.ArgumentParser("Sample Make")
    ap.add_argument("-p", "--project", required=False, default="", action="store", metavar="PROJ_NAME", help="build specific project only")
    ap.add_argument("-f", "--conf-file", required=False, default="SimpleMake.json", action="store", metavar="FILE", help="simple make config file")
    ap.add_argument("-c", "--clean-build", required=False, default=False, action="store_true", help="clean build directory")
    ap.add_argument("-C", "--clean-all", required=False, default=False, action="store_true", help="clean build and output directory")
    ap.add_argument("-v", "--version", required=False, default=False, action="store_true", help="show version")
    args = ap.parse_args(sys.argv[1:])

    if args.version == True:
        print('SimpleMake Version: ', SIMPLE_MAKE_VERSION)
        exit(0)

    # 读取配置文件
    print('read conf ...')
    smake_conf_file = args.conf_file
    if os.path.exists(smake_conf_file) == False:
        errorExit("conf file %s don't exist."%(smake_conf_file))

    f = open(smake_conf_file)
    smake_conf = f.read()
    smake_conf = json.loads(smake_conf)
    f.close()

    smake_conf, err_msg = checkConf(smake_conf)
    if err_msg != None:
        errorExit(err_msg)

    # 检查配置项的有效性，填入默认值，转换格式
    # 清理项目
    if os.path.exists(smake_conf[OPT_BUILD_DIR]):
        shutil.rmtree(smake_conf[OPT_BUILD_DIR])
    if args.clean_build == True:
            exit(0)
    if os.path.exists(smake_conf[OPT_OUTPUT_DIR]):
        shutil.rmtree(smake_conf[OPT_OUTPUT_DIR])
    if args.clean_all == True:
            exit(0)

    # 检查项目目录结构
    for project in smake_conf[OPT_PROJECTS]:
        project_name = project[OPT_NAME]
        if 'inc' in project[OPT_OUTPUT_TYPE]:
            if os.path.exists(project_name + '/inc/') == False:
                errorExit('"inc" directory not exist in project "%s"'%(project_name))
        if len(project[OPT_OUTPUT_TYPE].intersection({'exe', 'lib', 'dll'})) != 0:
            if os.path.exists(project_name + '/src/') == False:
                errorExit('"src" directory not exist in project "%s"'%(project_name))
            
    # 分析项目依赖，生成项目依赖项关系和项目构建顺序
    print('config build step ...')
    project_dependency = {} # {proj_name:[dep_proj_name ...]}
    build_order = []
    project_index = {} # {proj_name: idx_in_projects}
    index = 0
    # 生成项目依赖关系
    for project in smake_conf[OPT_PROJECTS]:
        project_name = project[OPT_NAME]
        project_index[project_name] = index
        index += 1
        build_order.append(project_name)
        if project_name in project_dependency:
            errorExit('project name repeate: ' + project[OPT_NAME])
        if OPT_DEPENDENCY in project:
            project_dependency[project_name] = project[OPT_DEPENDENCY]
        else:
            project_dependency[project_name] = []
    # 调整项目构建顺序
    # 对于每个项目，把依赖的项目移至自己的前面
    for proj_name in project_dependency:
        if len(project_dependency[proj_name]) != 0:
            proj_idx = list_find(build_order, proj_name)
            for dep_proj_name in project_dependency[proj_name]:
                dep_proj_idx = list_find(build_order, dep_proj_name)
                if dep_proj_idx == -1:
                    errorExit('dependency project not exist: ' + dep_proj_name)
                if dep_proj_idx > proj_idx:
                    list_move(build_order, dep_proj_idx, proj_idx)
                    proj_idx += 1

    # 依次构建项目
    build_dir = smake_conf[OPT_BUILD_DIR]
    output_dir = smake_conf[OPT_OUTPUT_DIR]
    if os.path.exists(build_dir) == False:
        os.mkdir(build_dir)
    if os.path.exists(output_dir) == False:
        os.mkdir(output_dir)
    for project in smake_conf[OPT_PROJECTS]:
        proj_name = project[OPT_NAME]
        print('\nbuilding project: ' + proj_name)
        # 非本地项目
        if project[OPT_CODE_LOCATION] == 'git':
            raise NotImplementedError('get code by git not functionable')
        proj_output_dir = output_dir + proj_name + '/'
        proj_build_dir = build_dir + proj_name + '/'
        if os.path.exists(proj_output_dir) == False:
            os.mkdir(proj_output_dir)
        if os.path.exists(proj_build_dir) == False:
            os.mkdir(proj_build_dir)
        # 有构建脚本
        if project[OPT_BUILD_SCRIPT] != '':
            raise NotImplementedError('build script not functionable')
        else:
            if project[OPT_PRE_BUILD_SCRIPT] != '':
                raise NotImplementedError('pre build script cannot exec.')
            # 获取项目构建信息
            proj_src_dir = proj_name + '/src/'
            need_compile = False
            need_copy_inc = False
            need_build_static = False
            need_build_dynamic = False
            need_link = False
            if 'inc' in project[OPT_OUTPUT_TYPE]:
                need_copy_inc = True
            if len(project[OPT_OUTPUT_TYPE].intersection({'exe', 'lib', 'dll'})) != 0:
                need_compile = True
            if 'lib' in project[OPT_OUTPUT_TYPE]:
                need_build_static = True
            if 'dll' in project[OPT_OUTPUT_TYPE]:
                need_build_dynamic = True
            if 'exe' in project[OPT_OUTPUT_TYPE]:
                need_link = True
            # 按需构建项目
            if need_compile:
                # 获取源文件列表
                c_files = get_file_by_suffix(proj_src_dir, {'c'})
                cxx_files = get_file_by_suffix(proj_src_dir, {'cpp', 'cc', 'cxx'})
                # 生成包含文件夹参数                
                include_args = ''
                proj_self_inc_dir = proj_name + '/inc/'
                if os.path.exists(proj_self_inc_dir):
                    include_args += ' -I ' + proj_self_inc_dir
                for dep_proj_name in project_dependency[proj_name]:
                    idx = project_index[dep_proj_name]
                    if 'inc' in smake_conf[OPT_PROJECTS][idx][OPT_OUTPUT_TYPE]:
                        include_args += ' -I ' + dep_proj_name + '/inc/'
                # 为动态库添加特殊编译选项
                compile_option = ''
                if 'dll' in project[OPT_OUTPUT_TYPE]:
                    compile_option += ' -fPIC'
                compile_option += project[OPT_COMPILE_OPTION]
                for file_name_info in c_files:
                    full_name = file_name_info[0]
                    base_name = file_name_info[1]
                    cmd_str = '%s -c -W%s%s %s -o %s'%(
                        project[OPT_C_COMPILER],
                        compile_option,
                        include_args,
                        proj_src_dir + full_name,
                        proj_build_dir + base_name + '.o')
                    printAndExecuteCmdStr(cmd_str, 'build failed.')
                for file_name_info in cxx_files:
                    full_name = file_name_info[0]
                    base_name = file_name_info[1]
                    cmd_str = '%s -c -W%s%s %s -o %s'%(
                        project[OPT_CXX_COMPILER],
                        compile_option,
                        include_args,
                        proj_src_dir + full_name,
                        proj_build_dir + base_name + '.o')
                    printAndExecuteCmdStr(cmd_str, 'build failed.')
            if need_link:
                # 获取依赖的项目中产出的库
                dependency_lib = ''
                for dep_proj_name in project_dependency[proj_name]:
                    idx = project_index[dep_proj_name]
                    if len(smake_conf[OPT_PROJECTS][idx][OPT_OUTPUT_TYPE].intersection({'lib', 'dll'})) > 0:
                        dependency_lib += ' ' + output_dir + dep_proj_name + '/' + smake_conf[OPT_PROJECTS][idx][OPT_OUTPUT_NAME]
                output_name = project[OPT_OUTPUT_NAME]
                cmd_str = '%s %s*.o%s -o %s'%(
                    smake_conf[OPT_LINKER], proj_build_dir, 
                    dependency_lib, output_name)
                printAndExecuteCmdStr(cmd_str, 'build failed.')
            if need_build_static:
                output_name = project[OPT_OUTPUT_NAME]
                cmd_str = 'ar -cr %s%s %s*.o'%(proj_output_dir, output_name, proj_build_dir)
                printAndExecuteCmdStr(cmd_str, 'build failed.')
            if need_build_dynamic:
                dependency_lib = ''
                for dep_proj_name in project_dependency[proj_name]:
                    idx = project_index[dep_proj_name]
                    if len(smake_conf[OPT_PROJECTS][idx][OPT_OUTPUT_TYPE].intersection({'lib', 'dll'})) > 0:
                        dependency_lib += ' ' + output_dir + dep_proj_name + '/' + smake_conf[OPT_PROJECTS][idx][OPT_OUTPUT_NAME]
                output_name = project[OPT_OUTPUT_NAME]
                cmd_str = '%s -shared %s*.o%s -o %s'%(smake_conf[OPT_DLL_BUILDER], proj_build_dir, dependency_lib, proj_output_dir + output_name)
                printAndExecuteCmdStr(cmd_str, 'build failed.')
            if need_copy_inc:
                shutil.copytree(proj_name + '/inc/', proj_output_dir + '/inc/')
            if project[OPT_POST_BUILD_SCRIPT] != '':
                raise NotImplementedError('post build script cannot exec.')

    # 构建结束
    print('Build success.')
                
