#CH5 在网站上分享内容

在上一章中，我们为网站创建了用户注册和权限功能。我们学习了如何为用户创建自定义profile模型并可以使用主要的社交网站账号登录网站。

在这一章中，我们将学习如何创建JavaScript bookmarklet实现自己的网站可以分享其它网站的内容，以及使用JQuery和Django实现AJAX特性。

这一章，我们将实现学习以下内容：

- 创建多对多关系

- 为表单自定义行为

- 在Django中使用jQuery

- 创建jQuery bookmarklet

- 使用sore-thumbnail 生成图像缩略图

- 实现AJAX视图并使用jQuery进行集成

- 为视图创建自定义装饰器

- 创建AJAX分页


## 创建一个图片标签网站

我们将允许用户为图像添加标签并分享他们在网站上找到的图片，以及在我们的网站上分享图片。为实现这个功能，我们需要完成以下工作：

1. 定义保存图像及其信息的模型；
2. 创建表单和视图来实现上传图片功能；
3. 创建用户可以发布从其他网站上找到的图片的系统。

首先，在bookmarks项目中新建一个应用：

```python 
django-admin startapp images
```

在项目的settings.py文件的INSTALLED_APPS中加入‘images’：

```
INSTALLED_APPS = ['account',
                  'django.contrib.admin',
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'social_django',
                  'images']
```

现在，Django知道新的应用已经激活了。

### 创建图片模型

编辑image应用的models.py模型并添加以下代码：

```python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models


# Create your models here.


class Image(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='images_created')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    url = models.URLField()
    image = models.ImageField(upload_to='images/%Y/%m/%d')
    description = models.TextField(blank=True)
    created = models.DateField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.title

```

这个模型用于保存从不同网站上得到的图片。让我们来看一下这个模型的字段：

user: 为这个图片进行标记的User对象。这是一个外键，它指定了一个一对多关系。一个用户可以发布多张图片，但是每个图片只有一个用户。

title：图片的标题。

slug：只包括字母、数字、下划线或者连字符来创建SEO友好的URLs。

url: 这个图片的原始url。

image：图片文件。

describe:可选的图片描述。

created：对象创建日期。由于我们使用了auto_now_add，当我们创建对象时会自动填充这个字段。我们使用db_index=True，这样Django将在数据库中为这个字段创建一个索引。

> 注意：
>
> 数据库索引将改善查询表现。对于频繁使用filter()、exclude()、order_by()进行查询的字段要设置db_index=True。外键字段或者unique=True的字段会自动设置索引。还可以使用Meta.index_together来为多个字段创建索引。


​     我们将重写Image模型的save()方法，来根据title字段自动生成slug字段。导入slugify()函数并为Image模型添加save()方法（还可以在admin网站中使用prepopulated_field告诉Django输入title时自动生成slug）：

```python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
# Create your models here.
from django.utils.text import slugify


class Image(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='images_created')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    url = models.URLField()
    image = models.ImageField(upload_to='images/%Y/%m/%d')
    description = models.TextField(blank=True)
    created = models.DateField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            super(Image, self).save(*args, **kwargs)

```

在这个代码中，如果用户没有提供slug，我们将slufigy()函数根据标题自动生成图像的slug。然后，我们保存对象。我们将自动生成slug，这样用户就不需要为每张图片填写slug字段了。

### 创建多对多关系

我们将在Image模型中添加一个字段来存储喜欢这张图片的用户。这种情况需要一个多对多关系，因为一个用户可能喜欢多张图片，而且每张图片可以被多个用户喜欢。

在Image模型中添加下面的字段：

```python 
users_like = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                    related_name='image_liked', blank=True)
```

当定义了一个多对多字段时，Django使用两个数据库表的主键创建了一个内联表。ManyToManyField可以位于两个相关模型中的任何一个模型中。

就像在ForeignKey字段中一样，ManyToManyField的related_name属性允许相关对象使用这个名字访问这个对象。ManyToManyField字段提供一个多对多管理器，这个管理器可以获取相关对象，比如image.user_liked.all()或者从用户端查询user.image_liked.all()。

打开命令行并执行以下命令：

```python 
python manage.py makemigrations images
```

我们将看到这样的输出：

```python
Migrations for 'images':
  images/migrations/0001_initial.py
    - Create model Image
```

现在运行以下命令实现迁移：

```python 
python manage.py migrate images
```

我们将看到这样的输出：

```python
Operations to perform:
  Apply all migrations: images
Running migrations:
  Applying images.0001_initial... OK
```

现在，Image模型同步到数据库中了。

### 在admin网站中注册image模型

编辑images应用的admin.py文件并在admin网站中注册Image模型：

```python 
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Image


# Register your models here.
class ImageAdmin(admin.ModelAdmin):
    list_display = ['titile', 'slug', 'image', 'created']
    list_filter = ['created']


admin.site.register(Image, ImageAdmin)

```

使用python manage.py runserver运行开发服务器。在浏览器中打开http://127.0.0.1:8000/admin，将在Admin网站中看到Image模型：

## 发布其他网站上的内容

我们将运行用户从外部网站标记image。用户将提供图像的URL、title并且可以进行描述。我们的应用将下载图片并在数据中创建新的Image对象。

我们从创建一个提交新图片的表单开始。在images应用目录下新建名为forms.py的文件并添加以下代码：

```python 
from django import forms

from .models import Image


class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('title', 'url', 'description')
        widgets = {'url': forms.HiddenInput, }

```

你可以看到，这个表单是一个根据IMage模型创建只包含title、url和description的ModelForm。用户不需要在表单中填入图片的URL。他们使用JavaScript工具从一个外部网站选择一个图片，我们的表单将以参数的形式获得这个图片的URL。我们重写了url字段的默认组件来使用HiddenInput组件。这个组件被渲染为一个具有type=‘hidden’属性的HTML输入元素。我们使用这个组件是因为不希望用户看到这个字段。

### 验证表单字段

为了保证提供的图片URL有效，我们将检查文件名是否以.jpg或者.jpeg结尾来只允许JPG文件的图片。Django允许用户通过定义表单方法clean_<filename>()来验证表单字段，当对表单实例调用is_valid()时，这些方法将对对应字段进行验证。在验证方法中，可以更改字段值或者为特定字段引发验证错误。在ImageCreateForm中添加以下代码：

```python 
def clean_url(self):
    url = self.cleaned_data['url']
    valid_extensions = ['jpg', 'jpeg']
    extension = url.rsplit('.', 1)[1].lower()
    if extension not in valid_extensions:
        raise forms.ValidationError(
            'The given URL does not match valid image extensions')
    return url
```

在上面的代码中，我们定义了clean_url()方法来验证url字段。代码这样工作:

1. 通过访问表单实例的cleaned_data字典获得url字段的值；
2. 截取URL获得文件扩展名并验证是否有效。如果该URL是一个无效的扩展名，将引发一个ValidationError并且表单无法通过验证。我们只是实现了一个非常简单的验证，你可以使用更高级的方法检查给定的URL是否提供了有效的图片文件。

除了验证给定的URL，我们还需要下载图片文件并保存。我们可以使用处理表单的视图来下载图片文件。这里我们使用更加通用的方法来实现，重写模型表单的save()方法在保存表单时实现下载。

### 重写ModelForm的save()方法

ModelForm提供一个save()方法来将当前模型实例保存到数据库中并返回该模型对象。这个方法接收一个布尔参数commit，这个参数指定是否需要提交到数据库。如果commit为False，save()方法将返回一个模型实例但是并不保存到数据库。我们将重写表单的save()方法来获得给定图片并保存。

在forms.py文件的开头部分添加以下imports：

```python 
from requests import request
from django.core.files.base import ContentFile
from django.utils.text import slugify
```

然后在ImageCreateForm中添加以下save()方法：

```python
def save(self,force_insert=False,force_update=False,commit=True):
    image = super(ImageCreateForm,self).save(commit=False)
    image_url = self.cleaned_data['url']
    image_name = '{}.{}'.format(slugify(image.title),image_url.split('.',1)[1].lower())
    # download image form given URL
    response = request('GET',image_url)
    image.image.save(image_name,ContentFile(response.content),save=False)
    if commit:
        image.save()
    return image
```

我们重写save()方法来保存ModelForm需要的参数，下面是代码如何执行的：

1. 我们通过调用commit设为False的save()方法获得image实例。
2. 从表单的cleaned_data字典中得到URL。
3. 结合image的名称slug和初始文件扩展名生成图片名称；
4. 使用Python的request库下载文件，然后调用image字段的save()方法，并向其传入一个ContentFile对象，这个ContentFile对象是下载的文件内容对象。这样我们将文件保存到项目的文件目录下。我们还可以传入save=False来避免保存到数据库。
5. 为了与重写前的save()方法保持一样的行为，只有在commit参数为True时将表单保存到数据库。

现在，我们需要一个视图来处理表单，编辑images应用的views.py文件，并添加以下代码：

```python 
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import ImageCreateForm


# Create your views here.

@login_required
def image_create(request):
    if request.method == 'POST':
        # form is sent
        form = ImageCreateForm(data=request.POST)
        if form.is_valid():
            # form data is valid
            cd = form.cleaned_data
            new_item = form.save(commit=False)

            # assign current user to the item
            new_item.user = request.user
            new_item.save()
            messages.success(request, 'Image added successfully')

            # redirect to new created item detail view
            return redirect(new_item.get_absolute_url())
    else:
        # build form with data provided by the bookmarklet via GET
        form = ImageCreateForm(data=request.GET)

    return render(request, 'images/image/create.html',
                  {'section': 'images', 'form': form})

```

我们为image_create视图添加了login_required装饰器来防止没有权限的用户访问。下面是视图的工作方法:

1. 我们通过GET方法得到初始数据来创建表单实例。这个数据将包含从外部网站获得的图片的url和title属性并通过我们之后创建的JavaScript工具的GET方法提供，这里我们只是假设在这里获得初始化数据。
2. 如果提交表单，我们将检查它是否有效。如果表单有效我们将创建一个新的image实例，但是设置commit=False来阻止将对象保存到数据库中。
3. 我们为新的image对象设置当前用户。这样我们就可以知道谁上传了这张image。
4. 将image对象保存到数据库。
5. 最终，我们使用Django的消息框架创建了成功消息并将用户重定向到新图片的URL。我们没有执行Image模型的get_absolute_url()方法，后续我们会使用它。

在images应用中新建urls.py文件并添加以下代码：

```python
from django.conf.urls import url

from . import views

urlpatterns = [(url(r'^create/$', views.image_create, name='create'),)]

```

编辑项目的urls.py文件并包含刚刚在images应用中新建的url模式：

```python 
urlpatterns = [url(r'^admin/', admin.site.urls),
               url(r'^account/',include('account.urls',namespace='account')),
               url(r'^', include('social_django.urls', namespace='social')),
               url(r'^images/',include('images.urls',namespace='images')),]
```

最后，我们需要新建模板来渲染表单。在image应用目录下新建下面的目录：



编辑create.html模板并添加以下代码：

```HTML
{% extends "base.html" %}

{% block title %}Bookmark an image{% endblock %}

{% block content %}
  <h1>Bookmark an image</h1>
  <img src="{{ request.GET.url }}" class="image-preview">
  <form action="." method="post">
    {{ form.as_p }}
    {% csrf_token %}
    <input type="submit" value="Bookmark it!">
  </form>
{% endblock %} 
```

现在，在浏览器中打开http://127.0.0.1:8000/images/create/?title=...&url=...，GET中包含或许提供的title和url参数。你可以使用以下URL的例子：http://127.0.0.1:8000/images/create/?title=%20Django%20and%20Duke&url=http://upload.wikimedia.org/wikipedia/commons/8/85/Django_Reinhardt_and_Duke_Ellington_%28Gottlieb%29.jpg.你将看到这样的图片和表单：



添加描述并点击Bookmark it!。数据库将保存一个新的图片对象。你可能会遇到一个模型没有get_absolute_url()方法的错误。现在不用管它，我们将在后面添加这个方法，在浏览器中打开 http://127.0.0.1:8000/admin/images/image/ 确定新的图片对象已经保存到数据库中了。

###使用jQuery创建bookmarklet

bookmarklet是浏览器中使用JavaScript代码扩展浏览器功能的书签。当你点击书签时，JavaScript代码将在浏览器显示的当前网页执行。这对于创建与其他网站进行交互的工具非常有帮助。

一些在线服务（比如Pinterest）执行自己的bookmarklet帮助用户将其他网站的内容分享到自己的平台上。我们将以相似的方式创建一个bookmarklet来帮助用户将从其它网站得到的图片分享到我们的网站上。

我们将使用jQuery实现bookmarklet。JQuery是一个用于快速开发客户端功能的JavaScript框架。你可以从它的网站上了解更多内容：http://jquery.com/。

下面是用户将如何在自己的浏览器中添加bookmarklet并使用：

1. 用户将链接拖到他的浏览器书签。链接在它的href属性中包含JavaScript代码。这些代码将被保存到书签中。

2. 用户浏览任何网站并点击书签，书签的JavaScript代码将执行。

由于JavaScript以书签的形式保存，你在之后无法对其进行更新。这个一个很重大的缺陷，但是可以通过执行简单的启动脚本从URL加载JavaScript代码来解决这个问题。你的用户将以书签的形式保存这个启动脚本，这样你可以在任意时刻更新bookmarklet。这是我们创建bookmarklet时采用的方法，让我们开始吧！

在image/templates/中新建模板并命名为marklet_launcher.js。这将是一个启动脚本，在脚本中添加以下JavaScript代码：



这个脚本通过检查是否定义了myBookmarklet变量来判断是否加载了bookmarklet。这样我们可以在用户重复点击bookmarklet的时候避免重复加载。如果没有定义myBookmarklet，我们加载另外一个JavaScript文件并向文件添加一个<script>元素。script标签使用随机数作为参数加载bookmark.js脚本以避免从浏览器缓存中加载文件。

真正的bookmarklet代码位于bookmarklet.js静态文件中。这将实现用户无需更新之前添加到浏览器中的书签即可更新bookmarklet代码的功能。我们将bookmarklet启动脚本添加到dashboard页面，这样用户可以拷贝到自己的书签中。

编辑account应用中的account/dashboard.html模板，最终模板的代码为：



拖到Bookmark it！连接到浏览器的书签工具条。

现在在images应用目录下创建以下目录和文件：



在本章代码中找到images application 目录下的static/css目录并将css目录拷贝到你的代码的static目录下，css/bookmarklet.css文件为我们的JavaScript bookmarklet提供格式。

编辑bookmarklet.js静态文件并添加以下JavaScript代码：

```javascript
(function () {
    var jquery_version = '2.1.4';
    var site_url = 'http://127.0.0.1:8000/';
    var static_url = site_url + 'static/';
    var min_width = 100;
    var min_height = 100;

    function bookmarklet(msg) {
        // Here goes our bookmarklet code
    };

    // Check if jQuery is loaded
    if (typeof window.jQuery != 'undefined') {
        bookmarklet();
    } else {
        // Check for conflicts
        var conflict = typeof window.$ != 'undefined';
        // Create the script and point to Google API
        var script = document.createElement('script');
        script.setAttribute('src',
            'http://ajax.googleapis.com/ajax/libs/jquery/' +
            jquery_version + '/jquery.min.js');
        // Add the script to the 'head' for processing
        document.getElementsByTagName('head')[0].appendChild(script);
        // Create a way to wait until script loading
        var attempts = 15;
        (function () {
            // Check again if jQuery is undefined
            if (typeof window.jQuery == 'undefined') {
                if (--attempts > 0) {
                    // Calls himself in a few milliseconds
                    window.setTimeout(arguments.callee, 250)
                } else {
                    // Too much attempts to load, send error
                    alert('An error ocurred while loading jQuery')
                }
            } else {
                bookmarklet();
            }
        })();
    }
})()
```

这是主要的jQuery加载器脚本。如果已经加载则在当前网站则使用jQuery，如果没有则从Google CDN中下载JQuery。当JQuery加载后，它将执行内置bookmarklet代码的bookmarklet()函数，我们还在文件头部设置了一些变量：

jquery_version：要加载的jQuery代码；

site_url和static_url：网站的基础URL和静态文件的基础URL。

min_width和min_height：bookmarklet在网站中查找图片的最小宽度像素和最小高度像素

现在，我们来执行bookmarklet函数，编辑bookmarklet()函数：

```javascript
function bookmarklet(msg) {
  // load CSS
  var css = jQuery('<link>');
  css.attr({
    rel: 'stylesheet',
    type: 'text/css',
    href: static_url + 'css/bookmarklet.css?r=' + Math.floor(Math.random()*99999999999999999999)
  });
  jQuery('head').append(css);

  // load HTML
  box_html = '<div id="bookmarklet"><a href="#" id="close">&times;</a><h1>Select an image to bookmark:</h1><div class="images"></div></div>';
  jQuery('body').append(box_html);

  // close event
  jQuery('#bookmarklet #close').click(function(){
     jQuery('#bookmarklet').remove();
  });
}
```

这些代码是这样工作的：

1. 使用随机数作为参数加载bookmarket.css样式以避免浏览器缓存。

2. 向当前网站的<body>元素中添加自定义HTML。它包含一个<div>元素来存放在当前网站中找到的图片。

3. 添加一个事件，该事件用于用户点击HTML块的关闭链接移除我们在当前网站中添加的HTML。我们使用#bookmarklet #close选择器来找到HTML元素中名为close的ID，这个ID的父元素的ID名称为bookmarklet。可以通过一个JQuery选择器找到HTML元素。一个JQuery选择器返回给定的CSS选择器找到的所有元素。你可以从以下网站找到JQuery选择器列表http://api.jquery.com/category/selectors/。

为bookmarklet加载完CSS样式和HTML代码后，我们需要在网站中找到图片。在bookmarklet()函数底部添加以下JavaScript代码：

```JavaScript
// find images and display them
jQuery.each(jQuery('img[src$="jpg"]'), function (index, image) {
    if (jQuery(image).width() >= min_width && jQuery(image).height() >= min_height) {
        image_url = jQuery(image).attr('src');
        jQuery('#bookmarklet .images').append('<a href="#"><img src="' + image_url + '" /></a>');
    }
});
```

代码使用`img[src$=“jpg”]`选择器找到所有<img>HTML元素，这些元素的src属性以jpg字符串结尾。这意味着我们将找到当前网站的所有JPG图片。我们使用jQuery的each方法对结果进行迭代。添加<div class='image'>HTML存放尺寸比min_width和min_height变量设置的尺寸大的图片。

现在HTML包含了所有可以添加标签的图片。我们希望用户点击期望的图片并添加标签。在bookmarklet()函数的底部添加以下代码：

```javascript
// when an image is selected open URL with it 
jQuery('#bookmarklet .images a').click(function (e) {
    selected_image = jQuery(this).children('img').attr('src');
    // hide bookmarklet
    jQuery('#bookmarklet').hide();
    // open new window to submit the image
    window.open(site_url + 'images/create/?url='
        + encodeURIComponent(selected_image)
        + '&title='
        + encodeURIComponent(jQuery('title').text()),
        '_blank');
});
```

这些代码的作用是：

1. 为图片链接元素绑定一个click()事件；

2. 当用户点击一个图片时，我们设置一个新的名为selected_image的变量来包含选中图片的URL；

3. 隐藏bookmarklet并使用URL打开一个新的浏览器窗口在我们的网站中编辑一个新的图片。我们以网站的<title>元素和选中的图片URL作为参数调用网站的GET方法。


在浏览器中打开一个网站并点击你的bookmarklet。你将看到一个新的白色盒子出现在网站中，他包含了网站中所有大于100*100px的照片。应该与下面例子中的样子很像：



由于我们使用的是Django开发服务器，并且通过HTTP为网页提供服务，由于浏览器的安全机制，bookmarklet将无法在HTTPS的网站中工作。

如果你点击一个图片，你将重定向到图片创建页面，输入网站的title和选择图片的描述作为GET参数：



祝贺你，这是你的第一个JavaScript bookmarklet，而且它已经继承到你的Django项目中了。

## 为图片创建一个详细视图

我们将创建一个简单地详细视图来展示保存到我们网站的图片。打开image应用的views.py文件并添加以下代码：

```python
from django.shortcuts import get_object_or_404
from .models import Image


def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug)
    return render(request, 'image/image/detail.html',
                  {'section': 'images', "image": image})
```

这是一个展示图片的简单视图。编辑image应用的urls.py文件，并添加以下URL模式：

```python 
               url(r'^detail/(?P<id>\d+)/(?P<slug>[-\w]+)/$',
                   views.image_detail, name='detail')]
```

编辑Image应用的models.py文件为Image模型增加get_absolute_url()方法：

```python 
from django.urls import reverse
def get_absolute_url(self):
    return reverse('images:detail', args=[self.id, self.slug])
```

为对象提供URL的常用做法为在它的模型中定义get_absolute_url()方法。

最后，我们在image应用的templates/image/image目录下新建名为detail.html文件，并添加以下代码：

```html
{% extends "base.html" %}

{% block title %}{{ image.title }}{% endblock %}

{% block content %}
    <h1>{{ image.title }}</h1>
    <img src="{{ image.image.url }}" class="image-detail">
    {% with total_likes=image.users_like.count %}
        <div class="image-info">
            <div>
        <span class="count">
          {{ total_likes }} like{{ total_likes|pluralize }}
        </span>
            </div>
            {{ image.description|linebreaks }}
        </div>
        <div class="image-likes">
            {% for user in image.users_like.all %}
                <div>
                    <img src="{{ user.profile.photo.url }}">
                    <p>{{ user.first_name }}</p>
                </div>
                {% empty %}
                Nobody likes this image yet.
            {% endfor %}
        </div>
    {% endwith %}
{% endblock %}”

```

这个模板展示标记的图片的详细信息。我们使用{% with %}标签通过total_likes变量来保存有多少人喜欢这幅图片的查询结果。这样，我们可以避免进行两次查询。我们还添加了图片描述并迭代image.users_like.all来展示喜欢这幅图片的人们。

注意：

使用{%with %}模板标签可以有效阻止Django多次进行数据库查询。

现在使用bookmarklet标记一副新的图片。当你提交图片后将重定向到图片详情页面。这个页面将包含如下的success信息。

## 使用sorl-thumbnail实现图片缩略图

我们在详情页面展示原始图片，但是不同图片的尺寸可能差别较大。而且一些图片的原始文件可能很大，加载它们可能需要很多时间。最好的方法展示使用相同的方法生成的缩略图。我们将使用Django应用sorl-thumbnail来实现缩略图。

打开terminal并使用如下命令安装sorl-thumbnail:

```python
pip install sorl-thumbnail
```

编辑bookmarks项目的settings.py文件并将sorl添加到INSTALLED_APPS中。

```python
INSTALLED_APPS = ['account',
                  'django.contrib.admin',
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'social_django',
                  'images',
                  'sorl']
```

然后运行下面的命令来同步数据库。

```python 
python manage.py migrate
```

你将看到下面的输出：

```
Operations to perform:
  Apply all migrations: account, admin, auth, contenttypes, images, sessions, social_django
Running migrations:
  No migrations to apply.
```

注意，这里没有同步任何数据库表，这与django by example不同。

sorl提供不同的方法定义图像缩略图。它提供一个{% thumbnail %}模板标签来在模板中生成缩略图，还可以使用自定义ImageField在模板中定义缩略图。我们将使用模板标签的方法。编辑image/image/detail.html模板将以下行：

```html
<img src="{{ image.image.url }}" class="image-detail">
```

替换为：

```html
{% load thumbnail %}
{% thumbnail image.image "300" as im %}
    <a href="{{ image.image.url }}">
        <img src="{{ im.url }}" class="image-detail">
    </a>
{% endthumbnail %}
```

现在，我们定义了宽度为300像素的缩略图。用户第一次加载页面时将会创建一个缩略图。生成的缩略图将用于后面的请求。输入python manage.py runserver命令运行开发服务器并访问一个存在的图片的图片详细信息页面，将会生成该图片的缩略图并在网站上展示。

sorl-thumbnail应用提供几个自定义缩略图的选项，包括图片剪裁算法和可以应用的不同效果。如果生成缩略图时遇到了困难，可以在settings.py中设置THUMBNAIL=True来得到调试信息。sorl-thumbnail的完整文档链接为http://sorl-thumbnail.readthedocs.org/。

## 使用jQuery添加AJAX动作

现在，我们开始在应用中添加AJAX动作。AJAX来源于异步JavaScript和XML(Asynchronous JavaScript and XML )。这个术语包含一组实现异步HTTP请求的技术。 它包括不用重新加载整个页面即可从服务器异步发送和检索数据。 尽管名字中包含XML，但是XML不是必需的。 您可以发送或检索其他格式的数据，如JSON、HTML或纯文本。

我们将在图片细节页面添加一个链接来实现用户可以通过点击该链接表示喜欢该图片。我们使用AJAX来实现这个动作以避免重新加载整个页面。首先，我们创建一个视图处理用户喜欢/不喜欢的信息。编辑images应用的views.py文件并添加以下代码：

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get('id')
    action = request.POST.get('action')
    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == 'like':
                image.users_like.add(request.user)
            else:
                image.users_like.remove(request.user)
            return JsonResponse({'status': 'ok'})
        except:
            pass
    return JsonResponse({'status': 'ko'})
```

我们为图片添加了两个装饰器。login_required装饰器阻止没有登录的用户访问该视图。如果没有通过POST方法访问该视图，required_POST装饰器返回一个HttpResponseNotAllowed对象（状态码为405)，这样我们只能通过POST请求访问该视图。Django还提供require_GET方法来只允许GET请求，require_http_method装饰器可以将允许的请求方法以参数的形式传入。

在这个视图中我们使用了两个POST关键词参数：

id: 用户操作的图片对象的ID；

action:用户的操作，应该是like或者unlike字符串。

我们使用Django为Image模型的多对多字段users_like提供的管理器的add()、remove()方法来为关系添加或者对象。调用add()传入相关对象集合中已经存在的对象并处理重复问题，调用remove()在相关对象集合中移除该对象。多对多管理器的另外一个很有用的方法是clear()，它将移除相关对象集合中的所有对象。

最后，我们使用Django提供的JsonResponse类（它将提供一个application/json格式的HTTP响应）将给定对象转换为JSON输出。

编辑image应用的urls.py并添加以下url模式：

```python
url(r'^like/$',views.image_like,name='like'),
```

### 加载jQuery

我们需要在image详细信息模板中添加AJAX函数。为了在模板中使用jQuery，我们首先将在base.html模板中加载它。编辑account应用中的base.html模板并在底端的</boday>HTML标签前添加以下代码：

```html
<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
<script>
    $(document).ready(function () {
        {% block domready %}
        {% endblock %}
    });
</script>
```

我们从Google加载了jQuery框架，在高速可靠的内容交付网络中托管流行的JavaScript框架。 您也可以从http://jquery.com/下载jQuery，并将其添加到您的应用程序的静态目录中。

我们添加了<script>标签来使用JavaScript代码，$(document).ready()是一个JQuery函数，它的功能是DOM层次结构构件完成后执行该函数包含的代码。加载网页时浏览器将创建DOM，它以对象树的形式构建。通过将我们的函数放到这个函数内可以保证我们交互所需要的HTML元素都已经包含在DOM中了。我们的代码只有在DOM加载完之后才能执行。

在$(document).ready()处理函数内容，我们使用了一个名为domready的模板块，这样扩展基础模板的模板可以使用特定的JavaScript。

不要将JavaScript代码和Django模板标签混淆在一起。Django模板语言在服务器侧渲染并输出最终的HTML，JavaScript在客户端执行。在某些案例中，使用Django动态生成JavaScript代码很有用。

> 注意:
>
> 在本章的例子中，我们将JavaScript代码放到Django模板中，更好的方法是通过.js文件（静态文件的一种）加载JavaScript代码，特别是在脚本比较大的情况下。

###AJAX请求的CSRF防护

我们已经在第二章中了解了CSRF防护。激活CSRF保护后，Django将检查所有POST请求的CSRF令牌(token)。提交表单时可以使用{% csrf_token %}模板标签与表单一起发送令牌。然而，AJAX请求在每个POST请求中以POST数据的形式传输CSRF令牌却有些麻烦。因此，Django允许我们早AJAX请求中使用CSRF令牌的值设置一个自定义的X-CSRFToken标头。这样可以使用jQuery或任何其他JavaScript库为每个请求自动设置X-CSRFToken标头。

为了所有的请求都包含令牌，我们需要:

1. 从csrftoken cookie中得到CSRF令牌，CSRF防护激活时将设置csrftoken cookie。
2. 在AJAX请求中使用X-CSRFToken标头发送令牌。

你可以在下面的网页找到更多关于CSRF防护和AJAX的信息https://docs.djangoproject.com/en/1.11/ref/csrf/#ajax。

编辑我们上次在base.html中添加的代码，使它看起来是这样的:

```javascript
<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
<script src=" http://cdn.jsdelivr.net/jquery.cookie/1.4.1/jquery.cookie.min.js "></script>
<script>
    var csrftoken = $.cookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    $(document).ready(function () {
        {% block domready %}
        {% endblock %}
    });
</script>
```

这些代码是这样工作的:

1. 从一个公共CDN加载jQuery cookie插件，这样我们可以与cookie交互。
2. 读取csrftoken的值；
3. 定义csrfSafeMethod()函数来检查一个HTTP方法是否安全。安全的方法（包括GET、HEAD、OPTIONS和TRACE）不需要CSRF防护。
4. 使用$.ajaxSetup()设置jQuery AJAX请求。实现每个AJAX请求时，我们检查请求方法是否安全记忆当前请求是否跨域。如果请求不安全，我们将使用从cookie中获取的值设置X-CSRFToken标头。jQuery的所有AJAX请求都将进行这种设置。

CSRF令牌将用在所有使用不安全的HTTP方法(比如POST、PUT)的AJAX请求中。

### 使用jQuery实现AJAX请求

编辑image应用的images/image/details.html模板并将以下行：

```
{% with total_likes=image.users_like.count %}
```

替换为：

```html
{% with total_likes=image.users_like.count,users_like=image.users_like.all %}
```

然后，将class为image-info的<div>更改为:

```html
<div class="image-info">
    <div>
        <span class="count">
            <span class="total">{{ total_likes }}</span>
            like{{ total_likes|pluralize }}
        </span>
        <a href="#" data-id="{{ image.id }}"
           data-action="{% if request.user in users_like %}un{% endif %}like"
           class="like button">
            {% if request.user not in users_like %}
                Like
            {% else %}
                Unlike
            {% endif %}
        </a>
    </div>
    {{ image.description|linebreaks }}
</div>
```

首先，我们在{% with %}模板标签中添加了另一个变量来保存image.users_like.all查询结果以避免重复执行。我们展示喜欢这个图片的用户数量和一个包含喜欢/不喜欢这张图片的连接：检查用户是否在users_like相关对象集合中来基于当前用户与图片的关系来展示喜欢或者不喜欢选项。我们向<a>元素添加下面的属性：

data-id: 展示的图片的ID；

data-action: 用户点击链接时执行的动作，可以是like或者unlike。

我们将这两个属性的值传入AJAX请求中。当用户点击like/unlike链接时，我们需要在用户端实现以下动作：

1. 调用AJAX视图传输图片的ID和动作参数；
2. 如果AJAX请求成功，使用相反的动作更新<a>HTML元素的data-action属性，并相应更改展示的文本。
3. 更改展示的like总数。

在images/image/detail.html模板底部添加domready块并添加以下JavaScript代码：

```javascript
{% block domready %}
    $('a.like').click(function(e){
        e.preventDefault();
        $.post(
            '{% url "images:like" %}',
            {
            id: $(this).data('id'),
            action: $(this).data('action')
            },
        function(data){
            if (data['status'] == 'ok'){
                var previous_action = $('a.like').data('action');

                // toggle data-action
                $('a.like').data('action', previous_action == 'like' ? 'unlike' : 'like');
                // toggle link text
                $('a.like').text(previous_action == 'like' ? 'Unlike' : 'Like');

                // update total likes
                var previous_likes = parseInt($('span.count .total').text());
                $('span.count .total').text(previous_action == 'like' ? previous_likes + 1 :
                previous_likes - 1);
            }
        });
    });
{% endblock %}
```

这些代码实现的操作是：

1. 使用`$('a.like')`选择器来找到HTML文档中class为like的<a>元素；
2. 为点击事件定义一个处理函数，这个函数将在每次用户点击like/unlike链接时触发；
3. 在处理函数内部，我们使用e.preventDefault()来避免<a>元素的默认行为。这样将避免链接将我们引导到其他地方。
4. 使用`$.post()`实现异步POST服务器请求。jQuery还提供`$.get()`方法来实现GET请求，以及小写的`$.ajax()`方法。
5. 使用{% url %}模板语言为AJAX请求创建URL。
6. 新建POST请求发送的参数字典，字典包括Django视图需要的ID和action参数。我们从<a>元素的data-id和data-action属性获得相应的值。
7. 定义接收HTTP响应的回调函数。它接收响应返回的参数。
8. 获取接收数据中的status属性并检查它是否等于'ok'。如果返回的data负荷预期，我们反转链接的data-action属性和文本。这将允许用户撤销操作。
9. 根据动作，增加或者减少一个喜欢这幅图片的人的数量。

在浏览器中打开你已经上传的图片的图片详细页面，你应该可以看到下面的初始喜欢数量和LIKE按钮：



点击LIKE按钮。你将看到总的喜欢数量增加了一个而且按钮变成了UNLIKE：



当你点击UNLIKE按钮后按钮变回LIKE并且总的喜欢数量相应发生改变。

当使用JavaScript编程，尤其是实现AJAX请求时，推荐使用Firebug之类的工具进行调试。Firebug是一个可以调试JavaScript并且可以监测CSS和HTML变化的FireFox插件。你可以从http://getfirebug.com下载FIrebug。其他的浏览器，比如Chrome或者Safari也提供内置开发工具来调试JavaScript。在这些浏览器中，你可以右击浏览器中的任何位置并点击Inspect element来访问web开发工具。



## 为视图创建自定义装饰器

我们将限制AJAX视图只允许AJAX请求，Django请求对象提供一个is_ajax()方法来判断请求是否是XMLHttpRequest生成的（这意味将是一个AJAX请求）。大多数JavaScript库的AJAX请求都包含的HTTP_X_REQUESTED_WITH HTTP标头设置这个值。

我们将创建一个装饰器来检查视图的HTTP_X_REQUESTED_WITH标头。一个装饰器是一个函数，它的作用为输入另一个函数并且在不改变另一个函数的基础上扩展它的行为。如果你不了解这个概念，你可以先看一个这个链接的内容https://www.python.org/dev/peps/pep-0318/。

由于装饰器是通用的，它可以用于任意视图上。我们将在项目中创建一个common Python文件。在bookmarket项目下新建以下文件结构：



编辑decorators.py文件并添加以下代码：

```python 
from django.http import HttpResponseBadRequest


def ajax_required(f):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

```

这就是我们的自定义ajax_required装饰器。它定义了一个wrap函数，如果不是AJAX请求则返回一个HttpResponseBadRequest对象（HTTP 400）。否则，它返回装饰器函数。

现在可以编辑images应用的views.py文件并在image_like AJAX视图上添加这个装饰器：

```python 
from common.decorators import ajax_required

@ajax_required
@login_required
@require_POST
def image_like(request):
```

如果在浏览器中尝试访问http://127.0.0.1:8000/images/like，将会得到一个HTTP 400响应。

> 注意：
>
> 如果发现在许多视图中重复同一项检查则为视图创建自定义装饰器。

## 为列表视图添加AJAX分页

如果需要在网站中列出所有标记的图片，我们将使用AJAX分页实现无限滚动功能。无限滚动是指当用户滚动到页面底部时自动加载其它结果。

我们将实现一个图片列表视图，该视图既可以处理标准浏览器请求，也可以处理包含分页的AJAX请求。用户第一次加载图像列表页面时，我们展示图像的第一页。当他滚动页面到最底部时我们通过AJAX加载后面页面的内容。

同一个视图将处理标准和AJAX分页。编辑image应用的views.py文件并添加以下代码：

```python 
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required
def image_list(request):
    images = Image.objects.all()
    paginator = Paginator(images, 8)
    page = request.GET.get('page')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        images = paginator.page(1)
    except EmptyPage:
        if request.is_ajax():
            # If the request is AJAX and the page is out of range
            # return an empty page
            return HttpResponse('')
        # If page is out of range deliver last page of results
        images = paginator.page(paginator.num_pages)
    if request.is_ajax():
        return render(request, 'images/image/list_ajax.html',
                      {'section': 'images', 'images': images})
    return render(request, 'images/image/list.html',
                  {'section': 'images', 'images': images})
```

在这个视图中，我们实现了一个queryset用来返回数据库中的所有图片。然后我们实现了一个Paginator对象按照每页八幅图片对结果进行分页。如果请求的页数已经超出分页页数则实现EmptyPage异常处理。如果请求通过AJAX实现则返回一个空的HttpResponse来帮助我们在客户端停止AJAX分页。我们使用两个不同的模板渲染结果:

- 对于AJAX请求，我们只渲染list_ajax.html模板，这个模板只包含请求的页面的图片。
- 对于标准请求，我们渲染list.html模板，这个模板将扩展base.html模板来展示整个页面，并且包含list_ajax.html模板来包含图片列表。

编辑images应用的urls.py文件并添加以下URL模式：

```python
url(r'^/$', views.image_list, name='list'),
```

最后，我们来实现上面提到的模板，在image/image模板目录下新建一个名为list_ajax.html的模板，并添加以下代码:

```html
{% load thumbnail %}

{% for image in images %}
    <div class="image">
        <a href="{{ image.get_absolute_url }}">
            {% thumbnail image.image "300x300" crop="100%" as im %}
                <a href="{{ image.get_absolute_url }}">
                    <img src="{{ im.url }}">
                </a>
            {% endthumbnail %}
        </a>
        <div class="info">
            <a href="{{ image.get_absolute_url }}" class="title">
                {{ image.title }}
            </a>
        </div>
    </div>
{% endfor %} 
```

这个模板展示图像列表。我们将用它来返回AJAX请求结果。在相同的目录下再新建一个名为list.html的模板，添加以下代码：

```HTML
{% extends "base.html" %}

{% block title %}Images bookmarked{% endblock %}

{% block content %}
    <h1>Images bookmarked</h1>
    <div id="image-list">
        {% include "images/image/list_ajax.html" %}
    </div>
{% endblock %}
```

这个模板扩展了base.html模板。为避免重复代码，我们将包含list_ajax.html模板来展示图片。list.html模板将包含滚轮滚动到底部时加载额外页面的JavaScript代码。

在list.html模板中添加以下代码：



```javascript
{% block domready %}
    var page = 1;
    var empty_page = false;
    var block_request = false;

    $(window).scroll(function() {
        var margin = $(document).height() - $(window).height() - 200;
        if  ($(window).scrollTop() > margin && empty_page == false && block_request
            == false) {
                block_request = true;
                page += 1;
                $.get('?page=' + page, function(data) {
                  if(data == '') {
                      empty_page = true;
                  }
                  else {
                      block_request = false;
                      $('#image-list').append(data);
                      }
            	});

        };
    });
{% endblock %}
```

这段代码实现了无限滚动功能。我们在base.html中定义的demready块中包含了JavaScript代码，代码实现的功能包括：

1. 定义以下变量：

   page：保存当前页码；

   empty_page：判断用户是否在最后一页并获取一个空页面。当我们获得一个空页面时表示没有其它结果了，我们将停止发送额外的AJAX请求。

   block_request：当处理一个AJAX请求时阻止发送额外请求；

2. 使用$(window).scroll()来获得滚动时间并为其定义一个处理函数；

3. 计算表示总文档高度和窗口高度的差的margin变量，这是用户可以滚动获得额外内容的高度。我们将结果减去200以便在用户接近底部200像素的位置加载下一页；

4. 我们只在没有实现其他AJAX请求（block_request需要为False)并且用户没有到达最后一个页面(empty_page为Flase)的情况下发送一个AJAX请求；

5. 我们将block_request设为True以避免滚动事件触发另一个AJAX请求，并将页面数增加1来获得另外一个页面；

6. 使用$.get()实现一个AJAX GET并将HTML响应返回到一个名为data的变量中，这里有两种情况：

   1. 响应没有内容，我们已经到了结果的底端没有更多页面需要加载了。我们设置empty_page为true来防止更多的AJAX请求；
   2. 响应包括数据：我们将数据添加到id为image-list的HTML元素底部。当用户到达页面底端时页面内容垂直扩展。

在浏览器中打开http://127.0.0.1:8000/images/。你将看到标记过的图片列表，看起来是这样的：





滚动到页面的底部来加载剩下的页面。确保你使用bookmarklet标记的图片多于8张，那是我们一页显示的图片数量。记得你可以使用Firebug或类似工具来追踪AJAX请求和调试JavaScript代码。

最后，编辑account应用的base.html模板并为主目录的Image记录添加URL：



现在可以从主目录访问图片列表了。

## 总结

在这一章，我们实现了JavaScript bookmarklet来从其他网站分享图片到自己的网站。并通过JQuery和添加AJAX分页实现了AJAX视图。

下一章将学习如何新建一个随动系统和一个活动流。你将使用通用关系、signals和demormalization。你还将学习如何在Django中使用Redis。

