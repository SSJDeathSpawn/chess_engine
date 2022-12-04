from typing import Union

DEFAULT_REGULAR_FONT: str = 'assets/fonts/IBMregular.ttf'
DEFAULT_ITALIC_FONT: str = 'assets/fonts/IBMitalic.ttf'
DEFAULT_BOLD_FONT: str = 'assets/fonts/IBMbold.ttf'
DEFAULT_BOLDITALIC_FONT: str = 'assets/fonts/IBMbolditalic.ttf'

CODE_FORMATTING: dict[str, str] = {

    'BLACK': '⸸{c:black}',
    'RED': '⸸{c:red}',
    'GREEN': '⸸{c:green}',
    'YELLOW': '⸸{c:yellow}',
    'BLUE': '⸸{c:blue}',
    'CYAN': '⸸{c:cyan}',
    'MAGENTA': '⸸{c:magenta}',
    'WHITE': '⸸{c:white}',
    'RESET': '⸸{c:reset}⸸{s:reset}',
    'REGULAR': '⸸{s:regular}',
    'BOLD': '⸸{s:bold}',
    'ITALIC': '⸸{s:italic}',
    'BOLD_ITALIC': '⸸{s:bold-italic}',

    'COLOR_RESET': '⸸{c:reset}',
    'STYLE_RESET': '⸸{s:reset}'

}

TEXT_CODES: dict[str, Union[tuple[int, int, int], str]] = {

    '⸸{c:black}': (0, 0, 0), 
    '⸸{c:red}': (255, 0, 0), 
    '⸸{c:green}': (0, 255, 0), 
    '⸸{c:yellow}': (255, 255, 0), 
    '⸸{c:blue}': (0, 0, 255), 
    '⸸{c:magenta}': (255, 0, 255), 
    '⸸{c:cyan}': (0, 255, 255), 
    '⸸{c:white}': (255, 255, 255),
    
    '⸸{s:regular}': 'regular', 
    '⸸{s:bold}': 'bold', 
    '⸸{s:italic}': 'italic',
    '⸸{s:bold-italic}': 'bolditalic'
    
}

TEXT_ESCAPE_CHAR: str = '⸸'
IBM_FNT_PT_FACTOR: tuple[float, float] = (3 / 5, 1)  # IBM Plex Mono Font size point conversion factors