from django.urls import path

from .views import status, keygen, sign, verify


urlpatterns = [

    # API 狀態檢查
    path(
        "status/",
        status,
        name="pqc-status"
    ),

    # ML-DSA-65 Key Generation
    path(
        "keygen/",
        keygen,
        name="pqc-keygen"
    ),

    # ML-DSA-65 Signing
    path(
        "sign/",
        sign,
        name="pqc-sign"
    ),

    # ML-DSA-65 Verification
    path(
        "verify/",
        verify,
        name="pqc-verify"
    ),

]