import cmd

class deployCLI(cmd.Cmd):
    primpt = '>>'
    intro = 'Welcome to MyCLI. Type "help" for available commands'


if __name__ == '__main__':
    deployCLI.cmdloop()