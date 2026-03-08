from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("panel_dashboard")
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        error = None

        if not username or not password:
            error = "Por favor ingresa usuario y contraseña."
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("panel_dashboard")
            else:
                error = "Credenciales incorrectas. Intenta de nuevo."

        return render(request, self.template_name, {"error": error})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("login")
