"""
Shell completion support for Prompy CLI.
"""

# Import needed functions from the codebase

# Shell completion script templates
BASH_COMPLETION_TEMPLATE = """
_prompy_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD \\
        _PROMPY_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"
        if [[ $type == 'dir' ]]; then
            COMPREPLY=( $(compgen -d -- "$value") )
        elif [[ $type == 'file' ]]; then
            COMPREPLY=( $(compgen -f -- "$value") )
        else
            COMPREPLY+=($value)
        fi
    done
    return 0
}

complete -o nosort -F _prompy_completion prompy
"""

ZSH_COMPLETION_TEMPLATE = """
#compdef prompy

_prompy_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[prompy] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" \\
        COMP_CWORD=$((CURRENT-1)) _PROMPY_COMPLETE=zsh_complete prompy)}")

    for type value description in ${response}; do
        if [[ "$type" == 'dir' ]]; then
            _path_files -/
        elif [[ "$type" == 'file' ]]; then
            _path_files -f
        elif [[ "$type" == 'plain' ]]; then
            if [[ -n "$description" ]]; then
                completions_with_descriptions+=("$value":"$description")
            else
                completions+=("$value")
            fi
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
    compstate[insert]="automenu"
}

compdef _prompy_completion prompy
"""

FISH_COMPLETION_TEMPLATE = """
function __fish_prompy_complete
    set -l response (env _PROMPY_COMPLETE=fish_complete \\
        COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) prompy)

    for completion in $response
        set -l name (string split --max 1 "," $completion)
        switch $name[1]
            case dir
                __fish_complete_directories $name[2]
            case file
                __fish_complete_path $name[2]
            case plain
                echo $name[2]
        end
    end
end

complete -c prompy -f -a "(__fish_prompy_complete)"
"""


def get_completion_script(shell: str) -> str:
    """
    Get the completion script for the specified shell.

    Args:
        shell: The shell type (bash, zsh, or fish)

    Returns:
        The shell completion script as a string
    """
    if shell == "bash":
        return BASH_COMPLETION_TEMPLATE.strip()
    elif shell == "zsh":
        return ZSH_COMPLETION_TEMPLATE.strip()
    elif shell == "fish":
        return FISH_COMPLETION_TEMPLATE.strip()
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def get_installation_instructions(shell: str) -> str:
    """
    Get the installation instructions for the completion script.

    Args:
        shell: The shell type (bash, zsh, or fish)

    Returns:
        Installation instructions as a string
    """
    if shell == "bash":
        return """
To enable bash completion, add this to your ~/.bashrc:

eval "$(_PROMPY_COMPLETE=bash_source prompy)"

Or, save the completion script and source it:

_PROMPY_COMPLETE=bash_source prompy > ~/.prompy-complete.bash
echo '. ~/.prompy-complete.bash' >> ~/.bashrc
"""
    elif shell == "zsh":
        return """
To enable zsh completion, add this to your ~/.zshrc:

eval "$(_PROMPY_COMPLETE=zsh_source prompy)"

Or, save the completion script and source it:

_PROMPY_COMPLETE=zsh_source prompy > ~/.prompy-complete.zsh
echo '. ~/.prompy-complete.zsh' >> ~/.zshrc
"""
    elif shell == "fish":
        return """
To enable fish completion, add this to your ~/.config/fish/config.fish:

eval (env _PROMPY_COMPLETE=fish_source prompy)

Or, save the completion script to the completions directory:

_PROMPY_COMPLETE=fish_source prompy > ~/.config/fish/completions/prompy.fish
"""
    else:
        raise ValueError(f"Unsupported shell: {shell}")
