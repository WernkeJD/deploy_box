import readchar
from .decorators import singleton

@singleton
class MenuHelper:
    def menu(
        self,
        data_options: list[str] = [],
        extra_options: list[str] = [],
        prompt: str = "Select an option: ",
    ):
        """Displays a menu where the user can navigate with arrow keys."""
        selected_idx = 0
        extra_options = extra_options + ["Cancel"]

        options = data_options + extra_options

        while True:
            print("\033c", end="")  # Clear screen

            if prompt:
                print(prompt)

            for i, option in enumerate(options):
                print(f"> {option}" if i == selected_idx else f"  {option}")

            key = readchar.readkey()

            if key == readchar.key.UP:
                selected_idx = (selected_idx - 1) % len(options)
            elif key == readchar.key.DOWN:
                selected_idx = (selected_idx + 1) % len(options)
            elif key == readchar.key.ENTER:
                break

        selected = options[selected_idx]

        if selected_idx >= len(data_options):
            selected_idx = selected_idx - len(data_options) - len(extra_options)

        return selected_idx, selected
