from PyQt6.QtWidgets import QApplication
from UI.Auth import Auth
from UI.UserUi import UserWindow

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    while True:
        auth = Auth()
        if auth.exec() != auth.DialogCode.Accepted:
            break

        userName, userRole, userId = auth.get_user_info()
        print(userName, userRole, userId)

        if userRole is None:
            window = UserWindow("Гость", "", userId)
        else:
            window = UserWindow(userName, userRole, userId)

        window.show()
        app.exec()

    sys.exit(0)
