import readchar

class MenuHelper:
    @staticmethod
    def menu(options, prompt="Select an option: "):
        """Displays a menu where the user can navigate with arrow keys."""
        selected = 0

        while True:
            print("\033c", end="")  # Clear screen

            if prompt:
                print(prompt)

            for i, option in enumerate(options):
                print(f"> {option}" if i == selected else f"  {option}")

            key = readchar.readkey()

            if key == readchar.key.UP:
                selected = (selected - 1) % len(options)
            elif key == readchar.key.DOWN:
                selected = (selected + 1) % len(options)
            elif key == readchar.key.ENTER:
                break

        return selected, options[selected]
