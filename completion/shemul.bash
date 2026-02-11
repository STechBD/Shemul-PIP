# bash completion for shemul
_shemul_complete() {
  local cur
  cur="${COMP_WORDS[COMP_CWORD]}"
  local opts
  opts=$(shemul _complete -- "${COMP_WORDS[@]:1}")
  COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
  return 0
}
complete -F _shemul_complete shemul
