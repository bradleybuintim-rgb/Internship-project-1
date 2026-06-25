from django.urls import path
from . import views

urlpatterns = [
    path('',               views.home,         name='home'),
    path('convert/',       views.convert,      name='convert'),
    path('convert/do/',    views.do_convert,   name='do_convert'),
    path('compress/',      views.compress,     name='compress'),
    path('compress/do/',   views.do_compress,  name='do_compress'),
    path('merge/',         views.merge,        name='merge'),
    path('merge/do/',      views.do_merge,     name='do_merge'),
    path('split/',         views.split,        name='split'),
    path('split/do/',      views.do_split,     name='do_split'),
    path('summarize/',     views.summarize,    name='summarize'),
    path('summarize/do/',  views.do_summarize, name='do_summarize'),
]