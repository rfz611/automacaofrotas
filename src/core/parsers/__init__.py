from core.parsers.base_parser import BaseParser, ParserIndisponivelError
from core.parsers.bradesco_parser import BradescoParser
from core.parsers.porto_seguro_parser import PortoSeguroParser
from core.parsers.tokio_marine_parser import TokioMarineParser

PARSERS_POR_SEGURADORA = {
    "BRADESCO": BradescoParser,
    "PORTO_SEGURO": PortoSeguroParser,
    "TOKIO_MARINE": TokioMarineParser,
}
