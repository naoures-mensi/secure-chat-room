import eel

eel.init('web')


@eel.expose
def my_python_function(a, b):
    print(a, b, a + b)
    return a + b;


eel.start('templates/index.html', jinja_templates='templates', mode='default')
