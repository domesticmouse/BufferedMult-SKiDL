# Prior Knowledge: Analog & Eurorack Electronics Foundation

The learner is already comfortable with core analog and Eurorack electronics concepts—including operational amplifiers, unity-gain voltage followers, local ceramic and bulk electrolytic decoupling, `±12V` bipolar power rails, and switched 3.5mm jacks—while seeking guided instruction on Python tooling (`uv`, decorators), KiCad 10 symbol/footprint mechanics, SKiDL circuit-as-code syntax, and programmatic component discovery.

## Evidence
- Disclosed directly during initial onboarding interview before Lesson `0001`.

## Implications
- Do not spend lesson time deriving op-amp feedback equations or explaining why bypass capacitors exist from first principles.
- Frame every circuit block by connecting the learner's existing analog intuition directly to its Python/SKiDL representation: how a `TL074` quad package maps to numeric pin indices (`u.p[1..14]`) vs. named power pins (`u["V+"]`, `u["V-"]`), how a switched jack's `T` / `TN` / `S` contacts wire into cascaded normalling nets, and how `part.fields` bridges Python objects to JLCPCB SMT manufacturing.
