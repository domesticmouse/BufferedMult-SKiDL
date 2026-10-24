# Teaching Notes & Learner Preferences

- **Goal**: Walk through building `buffered_multiple.py` in this repository from the ground up, with dedicated side tours into programmatic component, symbol, footprint, and JLCPCB/LCSC catalog discovery, toward designing and manufacturing custom Eurorack modules in Python.
- **Prior Knowledge**:
  - Comfortable with basic analog/Eurorack electronics (op-amps, unity-gain followers, ceramic/bulk decoupling, `±12V` rails, switched 3.5mm jacks).
  - Newer to Python packaging/idioms (`uv`, decorators like `@subcircuit`), KiCad symbol/footprint internals, SKiDL syntax, and programmatic LCSC/JLCPCB part lookup.
- **Pacing & Code Presentation Preference**:
  - **Self-Contained Code in Every Lesson (Start from Nothing & Grow It)**: Never assume the learner has another Python file open or is referencing an external file. Start from an empty file in Lesson `0000` and progressively grow the Python script across Lessons `0000` → `0001` → `0002` → `0003` → `0004`. Every lesson must explain each new code block as it is added AND include the complete, standalone, runnable Python script inline in the lesson HTML alongside its terminal output.
  - Accompany the lessons with printable reference sheets (`tutorial/reference/*.html`) and verified runnable scripts in `tutorial/apps/`.
