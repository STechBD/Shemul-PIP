# zsh completion for shemul
_shemul_complete() {
  local -a opts
  opts=(${(f)$(shemul _complete -- "${words[@]:1}")})
  _describe 'values' opts
}
compdef _shemul_complete shemul
