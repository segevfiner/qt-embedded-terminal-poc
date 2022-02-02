qt-embedded-terminal
====================
A POC of an embedded xterm.js terminal for Python Qt/PySide2 for Windows

Requires a custom pywinpty build using https://github.com/andfoy/winpty-rs/pull/16, and running
`npm install`.

## TODO
In case I ever want to make this more fully blown.

- Make it work on other OS than Windows by also supporting the standard `pty` module.
- Handle window resize so it doesn't leave a margin at the bottom of the window.
- Bundle resources.
- Minify/webpack.
- Include `xterm-addon-webgl`.
