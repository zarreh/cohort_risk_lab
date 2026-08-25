# Prompts

Versioned prompt files, referenced by id via `loader.load_prompt(id)` —
never inline strings in a node or chain. A prompt with an id and a version
can be diffed, regression-tested, and later optimised (A10); an f-string
embedded in code cannot.
