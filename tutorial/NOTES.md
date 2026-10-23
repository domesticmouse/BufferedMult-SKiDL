# Teaching Notes & Learner Preferences

- **Goal**: Walk through building `buffered_multiple.py` in this repository from the ground up, with dedicated side tours into programmatic component, symbol, footprint, and JLCPCB/LCSC catalog discovery, toward designing and manufacturing custom Eurorack modules in Python.
- **Prior Knowledge**:
  - Comfortable with basic analog/Eurorack electronics (op-amps, unity-gain followers, ceramic/bulk decoupling, `±12V` rails, switched 3.5mm jacks).
  - Newer to Python packaging/idioms (`uv`, decorators like `@subcircuit`), KiCad symbol/footprint internals, SKiDL syntax, and programmatic LCSC/JLCPCB part lookup.
- **Pacing Preference**:
  - Iterate lesson by lesson, starting with Lesson `0000` (Environment & KiCad 10 Bootstrap) and Lesson `0001` (Side Tour: Programmatic Part, Pinout & Footprint Discovery), accompanied by core reference sheets (`tutorial/reference/*.html`) and runnable scripts in `tutorial/apps/`.
