/*
 * main.cpp
 * Test runner for GUI
 * Only included in cmake Station render target
 */

#include "gui.h"
#include "mainloop.h"
#include "mesh.h"
#include "qmainwindow.h"
#include <QApplication>
#include <QEvent>
#include <QWindow>
#include <iostream>

class Filtery : public QObject {
  public:
    Filtery(Gui *gui) : gui(gui) {}

    Gui *gui;

    bool eventFilter(QObject *object, QEvent *event) {
        if (event->type() == GuiReadyEvent::event_number) {
            std::cout << "asdf" << std::endl;
            gui->setState(1, (DroneState)1);
            gui->setState(2, (DroneState)1);

            gui->setPos(1, 0, 0, 0);
            gui->setPos(2, 0, 10, 0);
            return true;
        } else {
            return false;
        }
    }
};

int main() {
    int argc = 0;
    char **argv;
    QApplication app(argc, argv);

    QMainWindow wind;

    Gui *gui = new Gui();
    wind.installEventFilter(new Filtery(gui));
    wind.setCentralWidget(gui);
    wind.show();

    app.exec();
}
