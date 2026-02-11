# fish completion for shemul
function __shemul_complete
  set -l opts (shemul _complete -- (commandline -opc))
  for o in $opts
    echo $o
  end
end
complete -c shemul -a "(__shemul_complete)"
