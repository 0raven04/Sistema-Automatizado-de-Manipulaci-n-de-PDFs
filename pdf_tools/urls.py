from django.urls import path
from .views.subida import SubidaPDFView
from .views.descarga import DescargarPDFView
from .views.merge import MergePDFView
from .views.split import SplitPDFView
from .views.rotate import RotatePDFView
from .views.watermark import WatermarkPDFView
from .views.generate import GeneratePDFView

urlpatterns = [
    path("upload/",   SubidaPDFView.as_view(),   name="subida"),
    path("download/", DescargarPDFView.as_view(), name="descarga"),
    path("merge/", MergePDFView.as_view(), name="merge"),
    path("split/", SplitPDFView.as_view(), name="split"),
    path("rotate/", RotatePDFView.as_view(), name="rotate"),
    path("watermark/", WatermarkPDFView.as_view(), name="watermark"),
    path("generate/", GeneratePDFView.as_view(), name="generate"),
]