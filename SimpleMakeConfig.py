import os.path

# 注意：所有的文件夹名称都以"/"结尾

DEFAULT_OUTPUT_DIR = './_output/'
DEFAULT_BUILD_DIR = './_build/'
DEFAULT_C_COMPILER = 'gcc'
DEFAULT_CXX_COMPILER = 'g++'
DEFAULT_LINKER = 'g++'
DEFAULT_DLL_BUILDER = 'g++'
DEFAULT_COMPILE_OPTION = ''
DEFAULT_PRE_BUILD_SCRIPT = ''
DEFAULT_POST_BUILD_SCRIPT = ''
OUTPUT_TYPE_SET = {'exe', 'lib', 'dll', 'inc'}
DEFAULT_GIT_ARGS = ''
DEFAULT_CODE_LOCATION = 'local'

CODE_LOCATION_SET = {'local', 'git'}

# 一级独有选项
OPT_SOLUTION_NAME = 'solution_name'
OPT_OUTPUT_DIR = 'output_dir'
OPT_BUILD_DIR = 'build_dir'
OPT_PROJECTS = 'projects'

# project选项
OPT_NAME = 'name'
OPT_CODE_LOCATION = 'code_location'
OPT_OUTPUT_TYPE = 'output_type'
OPT_OUTPUT_NAME = 'output_name'
OPT_DEPENDENCY = 'dependency'
OPT_BUILD_SCRIPT = 'build_script'
OPT_GIT_URL = 'git_url'
OPT_GIT_ARGS = 'git_args'
OPT_COMPILE_OPTION = 'compile_option'
OPT_LINK_OPTION = 'link_option'
OPT_PRE_BUILD_SCRIPT = 'pre_build_script'
OPT_POST_BUILD_SCRIPT = 'post_build_script'

# 一级选项和project共有选项
OPT_C_COMPILER = 'c_compiler'
OPT_CXX_COMPILER = 'cxx_compiler'
OPT_LINKER = 'ld'
OPT_DLL_BUILDER = 'gcc'

level_one_options = {OPT_SOLUTION_NAME, OPT_OUTPUT_DIR, OPT_BUILD_DIR, OPT_PROJECTS}
project_options = {OPT_NAME, OPT_CODE_LOCATION, OPT_OUTPUT_TYPE, OPT_OUTPUT_NAME, 
    OPT_DEPENDENCY, OPT_BUILD_SCRIPT, OPT_GIT_URL, OPT_GIT_ARGS, OPT_COMPILE_OPTION, 
    OPT_LINK_OPTION, OPT_PRE_BUILD_SCRIPT, OPT_POST_BUILD_SCRIPT}
shared_options = {OPT_C_COMPILER, OPT_CXX_COMPILER, OPT_LINKER, OPT_DLL_BUILDER}
level_one_options = level_one_options.union(shared_options)
project_options = project_options.union(shared_options)


# 检查mapp中是否存在key
# 不存在时设置mapp[key] = val
def setIfNonExist(mapp, key, val) :
    if key not in mapp:
        mapp[key] = val

# 检查配置项是否合法
# 并填入默认值，转换格式
# 返回值：(smake_conf, err_msg)，成功时err_msg为None，失败时smake_conf无效
def checkConf(smake_conf):
    for arg_name in smake_conf:
        if arg_name not in level_one_options:
            print('Warning: option "%s" is invalid, ignore it.'%(arg_name))
    setIfNonExist(smake_conf, OPT_OUTPUT_DIR, DEFAULT_OUTPUT_DIR)
    setIfNonExist(smake_conf, OPT_BUILD_DIR, DEFAULT_BUILD_DIR)
    setIfNonExist(smake_conf, OPT_C_COMPILER, DEFAULT_C_COMPILER)
    setIfNonExist(smake_conf, OPT_CXX_COMPILER, DEFAULT_CXX_COMPILER)
    setIfNonExist(smake_conf, OPT_LINKER, DEFAULT_LINKER)
    setIfNonExist(smake_conf, OPT_DLL_BUILDER, DEFAULT_DLL_BUILDER)
    if OPT_PROJECTS not in smake_conf \
        or type(smake_conf[OPT_PROJECTS]) != list:
        return(None, '"%s" is missing or error type in config file.'%(OPT_PROJECTS))
    if smake_conf[OPT_OUTPUT_DIR][-1] != '/' :
        return(None, 'option: "%s", directory name must end with "/"'%(OPT_OUTPUT_DIR))
    if smake_conf[OPT_BUILD_DIR][-1] != '/' :
        return(None, 'option: "%s", directory name must end with "/"'%(OPT_BUILD_DIR))

    i = 0
    for project in smake_conf[OPT_PROJECTS]:
        # 检查不存在的选项
        for option_name in project:
            if option_name not in project_options:
                print('Warning: option "%s" is invalid, ignore it.'%(option_name))
        if OPT_NAME not in project:
            return(None, '"%s" is missing in project info. project index:%d'%(OPT_NAME, i))
        setIfNonExist(project, OPT_CODE_LOCATION, DEFAULT_CODE_LOCATION)
        if project[OPT_CODE_LOCATION] not in CODE_LOCATION_SET:
            return(None, 'option %s:%s is illegal'%(OPT_CODE_LOCATION, project[OPT_CODE_LOCATION]))
        # 非本地代码
        code_location = project[OPT_CODE_LOCATION]
        if code_location == 'git':
            if OPT_GIT_URL not in project:
                return(None, '"%s" is missing in project info. project index:%d'%(OPT_GIT_URL, i))
            setIfNonExist(project, OPT_GIT_ARGS, DEFAULT_GIT_ARGS)
            raise NotImplementedError('code location git not ok yet')
        # 本地代码
        elif code_location == 'local':
            # 检查OPT_OUTPUT_TYPE的合法性，并转换成set类型
            if OPT_OUTPUT_TYPE not in project:
                return(None, '"%s" is missing in project info. project index:%d'%(OPT_OUTPUT_TYPE, i))
            for t in project[OPT_OUTPUT_TYPE]:
                if t not in OUTPUT_TYPE_SET:
                    return(None, 'output type "%s" is not supported'%(t))
            project[OPT_OUTPUT_TYPE] = set(project[OPT_OUTPUT_TYPE])
            if len(project[OPT_OUTPUT_TYPE].intersection({'exe', 'lib', 'dll'})) > 1 :
                return(None, 'exe, lib, dll, only choose one')
            # 有构建脚本的情况
            if OPT_BUILD_SCRIPT not in project:
                project[OPT_BUILD_SCRIPT] = ''
            if project[OPT_BUILD_SCRIPT] != '':
                continue
            # 常规构建
            setIfNonExist(project, OPT_C_COMPILER, smake_conf[OPT_C_COMPILER])
            setIfNonExist(project, OPT_CXX_COMPILER, smake_conf[OPT_CXX_COMPILER])
            setIfNonExist(project, OPT_LINKER, smake_conf[OPT_LINKER])
            setIfNonExist(project, OPT_DLL_BUILDER, smake_conf[OPT_DLL_BUILDER])
            setIfNonExist(project, OPT_PRE_BUILD_SCRIPT, DEFAULT_PRE_BUILD_SCRIPT)
            setIfNonExist(project, OPT_POST_BUILD_SCRIPT, DEFAULT_POST_BUILD_SCRIPT)
            setIfNonExist(project, OPT_COMPILE_OPTION, DEFAULT_COMPILE_OPTION)
            if project[OPT_COMPILE_OPTION] != '':
                project[OPT_COMPILE_OPTION] = ' ' + project[OPT_COMPILE_OPTION].strip()
            # 检查项目名称的有效性
            name = project[OPT_NAME]
            if os.path.exists('./' + name) == False:
                return(None, 'project directory not exist: %s'%(name))
            # 生成默认产出名称
            project_name = project[OPT_NAME]
            if OPT_OUTPUT_NAME not in project:
                if 'lib' in project[OPT_OUTPUT_TYPE]:
                    project[OPT_OUTPUT_NAME] = 'lib' + project_name + '.a'
                elif 'dll' in project[OPT_OUTPUT_TYPE]:
                    project[OPT_OUTPUT_NAME] = 'lib' + project_name + '.so'
                elif 'exe' in project[OPT_OUTPUT_TYPE]:
                    project[OPT_OUTPUT_NAME] = project_name                
        else:
            return(None, 'illegal code_location:%s. project index:%i'%(code_location, i))
        i += 1
    return (smake_conf, None)
