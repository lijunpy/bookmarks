# CH4 创建社交网站

在前面一章中，我们学习了如何创建sitemaps和feeds，并且为blog应用添加了搜索引擎。在这一章中，我们将实现用户登录、退出、编辑及重设密码。我们将学习如何创建自定义简介并为网站添加社交权限。

这一章将包含以下内容：

使用权限框架

创建用户注册视图

使用自定义简介模型扩展User模型

使用python-social-auth添加社交权限

我们从创建新的项目开始。

##创建一个社交网站项目

我们将创建一个社交应用来帮助用户分享他们在网上找到的图片。这个项目需要实现以下功能：

- 用户注册使用的权限系统，登录、编辑个人资料、更改或者重设密码；

- 关注系统来帮助用户相互关注；

- 展示分享的图片及帮助用户从任何网站分享图片的bookmarklet；

- 用户可以查看他关注的每个用户的动态。

本章我们将实现第一点。

### 启动社交网站项目

打开teminal并使用以下命令来为项目创建一个虚拟环境并激活：

```
mkdir env
virtualenv env/bookmarks
source env/bookmarks/bin/activate
```

shell将这样显示激活的虚拟系统：



在虚拟环境中使用以下命令安装Django：

```
 pip install django
```

运行以下命令并创建新的项目：

```
django-admin startporject bookmarks
```

创建完项目的初始结构后，使用以下命令进入项目目录并创建一个新的名为account的应用。

```
cd bookmarks/
django-admin startapp account
```

然后在项目settings.py文件的INSTALLED_APPS中第一行添加应用名称：





运行下一个命令来同步INSTALLED_APPS中默认应用的模型：

```
python manage.py migrate
```

我们将在项目中使用权限框架创建一个权限系统。

### 使用Django权限框架

Django内置可以处理用户权限、session、permission和用户分组的权限框架。权限系统包括登录、退出、更换密码、重设密码等常用操作的视图。

权限框架位于django.contrib.auth，该权限框架也用于contrib的其它部分。我们已经在第一章中使用过权限框架来创建超级用户以便访问blog应用的admin网站。

当使用starproject命令新建一个Django项目时，项目的默认设置已经包括权限框架。我们可以在settings.py的INSTALLED_APP中找到django.contrib.auth应用并且在MIDDLEWARE_CLASSES中找到以下中间件：

django.contrib.auth.middleware.AuthenticationMiddleware：使用session将用户与请求联系在一起；

django.contrib.sessions.middleware.SessionMiddleware：处理当前session。

middleware是一个包含在请求或响应过程中执行的函数的类。本书中我们有好几处使用middleware。你将在第十三章中学习如何新建自定义middleware。

权限框架包括以下模型;

User：用户模型，这个模型主要包括以下字段：username、password、email、first_name、last_name及is_active。

Group:用于用户分类的组模型；

Permission: 进行特定操作的标志位。

框架还包括后续需要使用的默认权限视图和表单。

### 创建一个登录视图

我们使用Django权限框架来允许用户登录网站。我们视图应该通过以下步骤实现用户登录：

1. 通过表单post获得用户名称及密码；

2. 通过数据库中的数据对用户进行认证；

3. 检查用户是否处与激活状态；

4. 登录到网站并开启一个授权的session。

  ​

首先，我们将创建一个登录表单。在account应用下新建一个名为forms.py文件并添加以下内容：


```python
from django import forms


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

```

这个表单将用于通过数据库对用户进行认证。注意，我们使用PasswordInput空间渲染它的HTML input元素，该控件包含一个type="password"属性。编辑account应用的views.py文件并添加以下代码：

```python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render

from .forms import LoginForm


# Create your views here.
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
        else:
            form = LoginForm()
            return render(request, 'account/login.html', {'form': form})
       
```

这是视图中基本登录的逻辑：当通过GET请求调用user_login视图时我们使用form=LoginForm()实例化一个新的登录表单并将其展示在模板中。当用户通过POST提交表单时，我们实现以下操作：

1. 通过form=LoginForm(request.POST)使用提交的数据对表单进行实例化；
2. 检查表单是否有效，如果无效（比如用户没有输入其中一个字段的内容）在模板中展示模板错误；
3. 如果提交的数据有效，我们使用authenticate()方法对用户进行验证。这个方法的输入为username和password，如果用户存在返回一个User对象，如果不存在则返回None。如果用户没有通过认证，我们将返回一个HttpResponse来显示信息。
4. 如果用户验证成功，我们将通过is_active属性检查用户是否处于激活状态，is_active属性时Django User模型的一个属性。如果用户没有激活，我们将放回一个HttpResponse来显示信息。
5. 如果用户已激活则可以登录。我们通过调用login()方法在session中设置用户并返回一个成功信息。

> 注意：
>
> 注意autheticate和login的区别:authenticate()验证用户，如果正确则返回用户对象；login()在当前session中设置用户。
>

现在，我们需要为视图创建URL模式。在account应用目录下创建一个新的urls.py文件并添加以下代码：

```python
from  django.conf.urls import url

from . import views

urlpatterns = [url(r'^login/$', views.user_login, name='login'),
    
]
```

编辑bookmarks下面的urls.py文件并添加accounts应用中的URL模式：

```python 

from django.conf.urls import url,include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^account/',include('account.urls')),
]
```

现在，可以通过URL访问师徒了。现在可以为视图创建模板了。由于这个项目不必包含任何模板，我们可以从创建登录模板可以扩展的基本模板开始。在account应用目录下新建以下文件和路径：





编辑base.html文件，并添加以下代码：



这将使网站的基准模板。正如上一个项目那样，我们将CSS放到主模板中，你可以从这节的代码中找到这些静态文件。将accounts应用的static目录拷贝到项目的相同位置，这样你就可以使用静态文件了。

基准模板定义了一个title和content block，扩展这个模板的其他模板可以填充这两个block。



我们来创建登录表单的模板，打开account/login.html模板并添加以下代码：





这个模板包含视图中实例化的表单。由于我们的表单将通过POST提交，我们将包含{% csrf_token %}模板标签来进行CSRF防护。我们在第二节中学习了CSRF防护。

现在数据库中还没有任何用户记录。我们需要首先创建一个superuser来登录admin网站并管理其他用户。在terminal的项目目录下输入以下命令：python manage.py createuser并填入相应的用户名、邮箱及密码。然后输入python manage.py runserver来运行开发服务器，并在浏览器中打开http://127.0.0.1:8000/admin/，使用刚刚创建的超级用户登录，你将看到Django admin网站上Django权限框架的User和Group模型，看起来是这样的：





使用admin网站创建一个新用户并浏览器中打开http://127.0.0.1:8000/account/login/，你将看到渲染过的包含登录表单的模板：



现在，在一个字段为空的情况下提交表单，这种情况下，我们将看到表单无法验证，界面会显示如下错误：





如果你输入了一个不存在的用户或者错误的密码，你将看到一个无效登录错误提示。

如果输入验证通过，我们将得到一个验证成功的信息：



### 使用Django权限视图

Django的权限框架包含几个可以直接使用的表单和视图。我们刚刚创建的登录视图是一个了解Django用户权限系统的很好的例子。然后，我们在大多数情况下可以直接使用Django的权限视图。

Django提供一下视图来处理权限问题：



Django提供一下视图来处理更改密码：



DJango提供一下视图来帮助用户重设密码：



创建网站的用户账户时上面的视图可以帮助我们节约很多时间。视图使用可以覆盖的默认值，比如需要渲染的模板的位置或者视图中使用的表单。

我们可以从以下网页得到更多关于内置权限视图的资料https://docs.djangoproject.com/en/1.11/topics/auth/default/#module-django.contrib.auth.views。

### 登录及退出登录视图





