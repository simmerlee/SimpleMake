# SimpleMake

## 简介
`SimpleMake`是一个简单、易用的C/C++项目构建工具。无序再写复杂的Makefile，只需编写简单的配置文件，SimpleMake即可分析项目依赖关系，自动构建项目。SimpleMake需要Python3来运行。

## 快速开始
假设有一个网络服务器程序，它包含2个项目，一个network相关的网络库，需要在构建后产出一个静态库，另一个是服务器自身的功能，需要链接network项目的静态库。目录结构如下：

    |---network/
    |   |---src/
    |   |   |---network.cpp
    |   |---inc/
    |       |---network.h
    |---server/
    |   |---src/
    |       |---server.cpp
    |---SimpleBuild.json

此时，只需一个简单的`SimpleBuild.json`配置文件即可让SimpleBuild正确地构建项目：
```json
{
    "projects":[
        {
            "name":"network",
            "output_type":["inc", "lib"]
        },
        {
            "name":"server",
            "output_type":["exe"],
            "dependency":["network"]
        }
    ]
}
```
在构建时，会自动给编译器传递依赖项目的头文件路径参数。构建结束后，会在当前文件夹下生成2个目录：`_build`和`_output`，期结构如下：

    |---_build/
    |   |---network/
    |   |   |---network.o
    |   |---server/
    |       |---server.o
    |---_output/
        |---network/
        |   |---inc/
        |   |   |---network.h
        |   |---libnetwork.a
        |---server/
            |---server

## 项目目录结构
SimpleMake采用类似Visual Studio的命名方法，一个解决方案由多个项目组成。解决方案文件夹内存有`SimpleMake.josn`配置文件，以及若干个项目文件夹。每个code_location为local的项目都必须有一个名字与项目名称相同的文件夹。项目文件夹内要有src文件夹，存放项目自身的代码。如果项目的output_type中包含inc、lib或dll，则还需要inc文件夹，存放需要导出的头文件。code_location为git的项目不需要项目文件夹。

## SimpleMake命令行参数
    smake [OPTIONS]
    -f, --conf-file     指定配置文件
    -p, --project       單獨構建指定項目，可以重複使用這個參數以指定多個項目
    -c, --clean-build   清除构建产生的中间文件
    -C, --clean-all     清除中间文件和产出
    -v, --version       版本号
    -h, --help          显示帮助信息

## SimpleMake.json配置文件
配置文件的格式为：
```json
{
    // 一级配置
    // ...
    "projects":[
        {
            "name":"xxx",
            "output_type":"exe"
        },
        {
            // ...
        }
    ]
}
```
### 一级配置
|选项|类型|必选|默认值|描述|
|---|---|---|---|---|
|solution_name|string||`""`|解决方案名称，不涉及构建流程，仅为了方便阅读|
|output_dir|string||`"./"`|构建结果保存的文件夹|
|build_dir|string||`"./"`|构建过程中的数据保存的文件夹|
|projects|list|是||解决方案包含的项目，包含至少一个project|
|c_compiler|string||`"gcc"`|可覆盖，C语言编译器，默认为gcc|
|cxx_compiler|string||`"g++"`|可覆盖，C++语言编译器，默认为g++|
|linker|string||`"ld"`|可覆盖，链接器|
|lib_builder|string||`"ar"`|可覆盖，静态库创建程序|
|dll_builder|string||`"gcc"`|可覆盖，动态库创建程序|
</br>

### project配置
|选项|类型|必选|默认值|描述|
|---|---|---|---|---|
|name|string|是||项目名称|
|code_location|string||`"local"`|代码所在位置，内容为local、git之一|
|output_type|string_list|是||项目产出的类型，内容为exe, inc, lib, dll的组合，用空格分隔|
|dependency|string_list||`[]`|项目依赖的项目的名称，只能依赖projects中的项目|
|compile_option|string||`"-W"`|传给编译器的编译参数，生成动态库时添加`-fPIC`参数|
|link_option|string||`""`|传给链接器的编译参数|
|*pre_build_script|string||`""`|构建项目前调用的脚本，空字符串表示无效。可使用相对路径或绝对路径，相对路径的当前路径为项目文件夹|
|*post_build_script|string||`""`|构建项目后调用的脚本，空字符串表示无效。可使用相对路径或绝对路径，相对路径的当前路径为项目文件夹|
|*build_script|string||`""`|自定义构建脚本文件名，空字符串表示无效。出现此参数时，使用项目文件夹内的构建脚本进行构建此项目，不再自动构建|
|*git_url|string|是||项目的git地址|
|*git_args|string||`""`|通过git获取项目代码时所需参数|
|一级配置中可覆盖的参数||||用法相同，优先使用项目配置中的参数|
</br>

code_location为local时，参数`git_url`、`git_args`无效。</br>
code_location为git时，`name`和git相关以外的参数都无效。</br>
build_script不为空时，`name`和其他选项都无效。</br>

带*的选项还未实现。


自定义构建脚本：
使用bash执行，会传入环境变量SMAKE_BUILD_DIR、SMAKE_OUTPUT_DIR


构建流程：
解析配置文件，创建相关文件夹，分析项目依赖，下载非本地项目（产出）
按顺序编译各个项目，并填写output、build文件夹