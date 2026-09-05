1.login:
method: post

url: https://swe.jzxhnh.com/api/v1/auth/login

body:
{"username":"shuaixianwei","password":"Ls317208!!"}

reponse:
{
    "code": 0,
    "message": "ok",
    "data": {
        "username": "shuaixianwei",
        "real_name": "帅先伟",
        "role": "USER",
        "is_first_login": false,
        "impersonated": false
    }
}

登录之后会有两个response header 返回作为以后的接口请求认证：
swe_qa_session=Who-swymDu4zUlFbCrOfcLu9ETCxB-cqVVyBfD6Hz4w; HttpOnly; Max-Age=43200; Path=/; SameSite=strict; Secure

swe_qa_csrf=REKlvW2ggvvbi5lwN5qVbQ1dtdZ4phwFOi9sTe6A2mc; Max-Age=43200; Path=/; SameSite=strict; Secure


以后的请求带上这两个cookies:
swe_qa_csrf: REKlvW2ggvvbi5lwN5qVbQ1dtdZ4phwFOi9sTe6A2mc
swe_qa_session: Who-swymDu4zUlFbCrOfcLu9ETCxB-cqVVyBfD6Hz4w
