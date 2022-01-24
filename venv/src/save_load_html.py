import pickle,sys

def save_obj(html, filename):
    with open(filename, 'wb') as f:
        f.write(html)

def load_obj(filename):
    with open(filename, 'rb') as f:
        return f.read()