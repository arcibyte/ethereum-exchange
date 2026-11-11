import json
import re
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "notebooks" / "Proyecto_Final_Colab.ipynb"


def leer_modulo(nombre):
    texto = (RAIZ / "src" / nombre).read_text(encoding="utf-8")
    # En una celda no hace falta el future import y puede molestar.
    texto = texto.replace("from __future__ import annotations\n\n", "")
    texto = texto.replace("from __future__ import annotations\n", "")
    return texto.strip("\n")


def md(texto):
    return {
        "cell_type": "markdown",
        "id": uuid.uuid4().hex[:8],
        "metadata": {},
        "source": texto.strip("\n").splitlines(keepends=True),
    }


def limpiar_comentarios(texto: str) -> str:
    """Quita separadores decorativos tipo `# ============ ...`."""
    lineas = []
    for linea in texto.splitlines():
        limpia = linea.strip()
        if limpia.startswith("#") and ("====" in limpia or "----" in limpia):
            continue
        lineas.append(linea)
    return "\n".join(lineas)


def code(texto):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": uuid.uuid4().hex[:8],
        "metadata": {},
        "outputs": [],
        "source": limpiar_comentarios(texto).strip("\n").splitlines(keepends=True),
    }


seccion1_md = ""
seccion1_code = ""

carga_md = "## Cargar el dataset\n\nSube **un solo archivo**:\n\n```\ntransferencias.parquet\n```\n\nPuedes dejarlo en cualquiera de estas rutas:\n\n```\n/content/transferencias.parquet\nMi unidad/ED2/transferencias.parquet\ndata/procesado/transferencias.parquet\n```\n\nLa celda busca el archivo, genera una muestra de USDC y construye el grafo\nque usan las Tareas 1–4.\n\n> Si estás en Colab, también puedes subirlo con **Archivo → Subir** o con:\n>\n> ```python\n> # from google.colab import files\n> # files.upload()\n> ```"
carga_datos = "# ============ RUTAS Y CARGA DEL DATASET ============\nimport os\nfrom collections import defaultdict, deque\n\nCARPETA_DRIVE = \"/content/drive/MyDrive/ED2\"\nCARPETA_LOCAL = \"data\"\n\nUSDC = \"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48\"\nCERO = \"0x0000000000000000000000000000000000000000\"\n\n\ndef buscar_archivo(*rutas):\n    \"\"\"Devuelve la primera ruta que exista, o None si no existe ninguna.\"\"\"\n    for ruta in rutas:\n        if ruta and os.path.isfile(ruta):\n            return ruta\n    return None\n\n\nRUTA_PARQUET = buscar_archivo(\n    \"/content/transferencias.parquet\",\n    f\"{CARPETA_DRIVE}/transferencias.parquet\",\n    f\"{CARPETA_LOCAL}/procesado/transferencias.parquet\",\n)\n\nprint(\"Parquet encontrado:\", RUTA_PARQUET)\n\nif RUTA_PARQUET is None:\n    raise FileNotFoundError(\n        \"No encontré transferencias.parquet. Súbelo a /content/ o a \"\n        \"Mi unidad/ED2/transferencias.parquet.\"\n    )\n\n\ndef componente_mayor(aristas):\n    \"\"\"Conserva solo las aristas de la componente conexa más grande.\"\"\"\n    adyacencia = defaultdict(set)\n    for origen, destino, _ in aristas:\n        adyacencia[origen].add(destino)\n        adyacencia[destino].add(origen)\n\n    visitados = set()\n    mejor = set()\n\n    for inicio in adyacencia:\n        if inicio in visitados:\n            continue\n\n        componente = set()\n        cola = deque([inicio])\n        visitados.add(inicio)\n\n        while cola:\n            nodo = cola.popleft()\n            componente.add(nodo)\n            for vecino in adyacencia[nodo]:\n                if vecino not in visitados:\n                    visitados.add(vecino)\n                    cola.append(vecino)\n\n        if len(componente) > len(mejor):\n            mejor = componente\n\n    return [\n        (origen, destino, peso)\n        for origen, destino, peso in aristas\n        if origen in mejor and destino in mejor\n    ]\n\n\ndef muestra_desde_parquet(ruta):\n    \"\"\"Genera una muestra de USDC desde el Parquet.\"\"\"\n    try:\n        import duckdb\n    except ImportError:\n        import subprocess\n        import sys\n        subprocess.run(\n            [sys.executable, \"-m\", \"pip\", \"install\", \"-q\", \"duckdb\", \"pyarrow\"],\n            check=True,\n        )\n        import duckdb\n\n    con = duckdb.connect()\n    con.execute(\"SET memory_limit='2GB'\")\n    con.execute(\"SET threads=2\")\n\n    filas = con.execute(\n        \"\"\"\n        SELECT from_address, to_address, value\n        FROM read_parquet(?)\n        WHERE token_address = ?\n        USING SAMPLE reservoir(65000 ROWS) REPEATABLE (42)\n        \"\"\",\n        [ruta, USDC],\n    ).fetchall()\n\n    aristas = []\n    for origen, destino, valor in filas:\n        origen = str(origen).lower()\n        destino = str(destino).lower()\n        valor = float(valor) / 1e6\n\n        if not origen or not destino or origen == destino:\n            continue\n        if origen == CERO or destino == CERO:\n            continue\n        if valor <= 0:\n            continue\n\n        aristas.append((origen, destino, valor))\n\n    return componente_mayor(aristas)\n\n\naristas = muestra_desde_parquet(RUTA_PARQUET)\n\ngrafo = Grafo()\nfor origen, destino, peso in aristas:\n    grafo._agregar_arista(origen, destino, peso, limpiar=False)\n\nprint(\"Muestra generada desde el Parquet:\")\nprint(\"  nodos   :\", len(grafo.nodos))\nprint(\"  aristas :\", len(grafo.aristas))\nprint(\"  resumen :\", grafo.resumen())"

drive_md = "## 1. Conectar con Google Drive\n\nEsta celda monta Google Drive para poder leer el dataset desde\n`Mi unidad/ED2/`. En local se salta sola.\n"
drive_code = "# ============ MONTAR GOOGLE DRIVE (COLAB) ============\ntry:\n    from google.colab import drive\n    drive.mount(\"/content/drive\")\nexcept Exception as exc:\n    print(\"Drive no disponible (normal si estás en local):\", exc)\n"

etiquetas_md = "### Etiquetas de exchanges\n\nEl Parquet no trae nombres, solo direcciones. Estas 296 etiquetas son metadatos\ndel dataset original y permiten que Louvain y PageRank muestren nombres como\n`Binance 1`, `FTX Exchange` o `1inch.exchange` en lugar de direcciones.\n\nLas etiquetas son parciales: no todas las direcciones tienen nombre.\n"
etiquetas_code = "# ============ ETIQUETAS DE EXCHANGES ============\n# Metadatos del dataset original: dirección -> nombre y tipo.\nETIQUETAS = {\n    \"0x11111254369792b2ca5d084ab5eea397ca8fa48b\": {\n        \"nombre\": \"1inch.exchange\",\n        \"tipo\": \"dex\"\n    },\n    \"0xe8fff15bb5e14095bfdfa8bb85d83cc900c23c56\": {\n        \"nombre\": \"AfroDex\",\n        \"tipo\": \"dex\"\n    },\n    \"0x4572f2554421bd64bef1c22c8a81840e8d496bea\": {\n        \"nombre\": \"AirSwap\",\n        \"tipo\": \"dex\"\n    },\n    \"0xdc1882f350b42ac9a23508996254b1915c78b204\": {\n        \"nombre\": \"Allbit 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0xff6b1cdfd2d3e37977d7938aa06b6d89d6675e27\": {\n        \"nombre\": \"Allbit 2\",\n        \"tipo\": \"dex\"\n    },\n    \"0x0e8ba001a821f3ce0734763d008c9d7c957f5852\": {\n        \"nombre\": \"AmadeusRelay\",\n        \"tipo\": \"dex\"\n    },\n    \"0xc898fbee1cc94c0ff077faa5449915a506eff384\": {\n        \"nombre\": \"Bamboo Relay\",\n        \"tipo\": \"dex\"\n    },\n    \"0x3c020e014069df790d4f4e63fd297ba4e1c8e51f\": {\n        \"nombre\": \"Bitcratic\",\n        \"tipo\": \"dex\"\n    },\n    \"0x39fbd1140cd1fc298f00c3ea64b3591de94c67e7\": {\n        \"nombre\": \"BitEye 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0xb5adb233f28c86cef693451b67e1f2d41da97d21\": {\n        \"nombre\": \"Bitox.io\",\n        \"tipo\": \"dex\"\n    },\n    \"0xe269e891a2ec8585a378882ffa531141205e92e9\": {\n        \"nombre\": \"DDEX\",\n        \"tipo\": \"dex\"\n    },\n    \"0x49497a4d914ae91d34ce80030fe620687bf333fd\": {\n        \"nombre\": \"DDEX 1.0\",\n        \"tipo\": \"dex\"\n    },\n    \"0xaf8ae6955d07776ab690e565ba6fbc79b8de3a5d\": {\n        \"nombre\": \"DeversiFi\",\n        \"tipo\": \"dex\"\n    },\n    \"0x745daa146934b27e3f0b6bff1a6e36b9b90fb131\": {\n        \"nombre\": \"DEX.AG: Proxy Contract\",\n        \"tipo\": \"dex\"\n    },\n    \"0x000000000000541e251335090ac5b47176af4f7e\": {\n        \"nombre\": \"dex.blue\",\n        \"tipo\": \"dex\"\n    },\n    \"0x7600977eb9effa627d6bd0da2e5be35e11566341\": {\n        \"nombre\": \"DEx.top\",\n        \"tipo\": \"dex\"\n    },\n    \"0x268be5667d4e5bd036bd608d0601ef1441604429\": {\n        \"nombre\": \"DINNGO: Proxy\",\n        \"tipo\": \"dex\"\n    },\n    \"0x58a5959a6c528c5d5e03f7b9e5102350e24005f1\": {\n        \"nombre\": \"ERC dEX\",\n        \"tipo\": \"dex\"\n    },\n    \"0x4aea7cf559f67cedcad07e12ae6bc00f07e8cf65\": {\n        \"nombre\": \"EtherDelta 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0x8d12a197cb00d4747a1fe03395095ce2a5cc6819\": {\n        \"nombre\": \"EtherDelta 2\",\n        \"tipo\": \"dex\"\n    },\n    \"0xa5cc679a3528956e8032df4f03756c077c1ee3f4\": {\n        \"nombre\": \"EtherMium\",\n        \"tipo\": \"dex\"\n    },\n    \"0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208\": {\n        \"nombre\": \"IDEX 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0xa7a7899d944fe658c4b0a1803bab2f490bd3849e\": {\n        \"nombre\": \"IDEX 2\",\n        \"tipo\": \"dex\"\n    },\n    \"0x2cc42d1cd65af27cc999e41ef93d1a763dc821f8\": {\n        \"nombre\": \"IDT Exchange\",\n        \"tipo\": \"dex\"\n    },\n    \"0x04f062809b244e37e7fdc21d9409469c989c2342\": {\n        \"nombre\": \"Joyso\",\n        \"tipo\": \"dex\"\n    },\n    \"0x05f51aab068caa6ab7eeb672f88c180f67f17ec7\": {\n        \"nombre\": \"ABCC\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2ddd202174a72514ed522e77972b461b03155525\": {\n        \"nombre\": \"Alcumex Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf0c80fb9fb22bef8269cb6feb9a51130288a671f\": {\n        \"nombre\": \"Artis Turba Exchange 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x94597850916a49b3b152ee374e97260b99249f5b\": {\n        \"nombre\": \"Artis Turba Exchange 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4df5f3610e2471095a130d7d934d551f3dde01ed\": {\n        \"nombre\": \"ATAIX\",\n        \"tipo\": \"cex\"\n    },\n    \"0xadb72986ead16bdbc99208086bd431c1aa38938e\": {\n        \"nombre\": \"Beaxy\",\n        \"tipo\": \"cex\"\n    },\n    \"0x7a10ec7d68a048bdae36a70e93532d31423170fa\": {\n        \"nombre\": \"Bgogo 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xce1bf8e51f8b39e51c6184e059786d1c0eaf360f\": {\n        \"nombre\": \"Bgogo 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf73c3c65bde10bf26c2e1763104e609a41702efe\": {\n        \"nombre\": \"Bibox\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0bb5de248dbbd31ee6c402c3c4a70293024acf74\": {\n        \"nombre\": \"Bidesk 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xed5cdb0d02152046e6f234ad578613831b9184d4\": {\n        \"nombre\": \"Bidesk 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa30d8157911ef23c46c0eb71889efe6a648a41f7\": {\n        \"nombre\": \"BigONE\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6eff3372fa352b239bb24ff91b423a572347000d\": {\n        \"nombre\": \"BIKI.com 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf7793d27a1b76cdf14db7c83e82c772cf7c92910\": {\n        \"nombre\": \"Bilaxy 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xcce8d59affdd93be338fc77fa0a298c2cb65da59\": {\n        \"nombre\": \"Bilaxy 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be\": {\n        \"nombre\": \"Binance 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd551234ae421e3bcba99a0da6d736074f22192ff\": {\n        \"nombre\": \"Binance 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x564286362092d8e7936f0549571a803b203aaced\": {\n        \"nombre\": \"Binance 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0681d8db095565fe8a346fa0277bffde9c0edbbf\": {\n        \"nombre\": \"Binance 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfe9e8709d3215310075d67e3ed32a380ccf451c8\": {\n        \"nombre\": \"Binance 5\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67\": {\n        \"nombre\": \"Binance 6\",\n        \"tipo\": \"cex\"\n    },\n    \"0xbe0eb53f46cd790cd13851d5eff43d12404d33e8\": {\n        \"nombre\": \"Binance 7\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf977814e90da44bfa03b6295a0616a897441acec\": {\n        \"nombre\": \"Binance 8\",\n        \"tipo\": \"cex\"\n    },\n    \"0x001866ae5b3de6caa5a51543fd9fb64f524f5478\": {\n        \"nombre\": \"Binance 9\",\n        \"tipo\": \"cex\"\n    },\n    \"0xab83d182f3485cf1d6ccdd34c7cfef95b4c08da4\": {\n        \"nombre\": \"Binance JEX\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4b729cf402cfcffd057e254924b32241aedc1795\": {\n        \"nombre\": \"Bit-Z\",\n        \"tipo\": \"cex\"\n    },\n    \"0x7c49e1c0e33f3efb57d64b7690fa287c8d15b90a\": {\n        \"nombre\": \"Bit2C\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5d375281582791a38e0348915fa9cbc6139e9c2a\": {\n        \"nombre\": \"BitBlinx\",\n        \"tipo\": \"cex\"\n    },\n    \"0x28ebe764b8f9a853509840645216d3c2c0fd774b\": {\n        \"nombre\": \"BiteBTC\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1151314c646ce4e0efd76d1af4760ae66a9fe30f\": {\n        \"nombre\": \"Bitfinex 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x742d35cc6634c0532925a3b844bc454e4438f44e\": {\n        \"nombre\": \"Bitfinex 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x876eabf441b2ee5b5b0554fd502a8e0600950cfa\": {\n        \"nombre\": \"Bitfinex 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xab7c74abc0c4d48d1bdad5dcb26153fc8780f83e\": {\n        \"nombre\": \"Bitfinex: MultiSig 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xc6cde7c39eb2f0f0095f41570af89efc2c1ea828\": {\n        \"nombre\": \"Bitfinex: MultiSig 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xdf5021a4c1401f1125cd347e394d977630e17cf7\": {\n        \"nombre\": \"BITFRONT\",\n        \"tipo\": \"cex\"\n    },\n    \"0x88d34944cf554e9cccf4a24292d891f620e9c94f\": {\n        \"nombre\": \"Bithumb 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x186549a4ae594fc1f70ba4cffdac714b405be3f9\": {\n        \"nombre\": \"Bithumb 10\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd273bd546b11bd60214a2f9d71f22a088aafe31b\": {\n        \"nombre\": \"Bithumb 11\",\n        \"tipo\": \"cex\"\n    },\n    \"0x3052cd6bf951449a984fe4b5a38b46aef9455c8e\": {\n        \"nombre\": \"Bithumb 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2140efd7ba31169c69dfff6cdc66c542f0211825\": {\n        \"nombre\": \"Bithumb 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa0ff1e0f30b5dda2dc01e7e828290bc72b71e57d\": {\n        \"nombre\": \"Bithumb 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0xc1da8f69e4881efe341600620268934ef01a3e63\": {\n        \"nombre\": \"Bithumb 5\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb4460b75254ce0563bb68ec219208344c7ea838c\": {\n        \"nombre\": \"Bithumb 6\",\n        \"tipo\": \"cex\"\n    },\n    \"0x15878e87c685f866edfaf454be6dc06fa517b35b\": {\n        \"nombre\": \"Bithumb 7\",\n        \"tipo\": \"cex\"\n    },\n    \"0x31d03f07178bcd74f9099afebd23b0ae30184ab5\": {\n        \"nombre\": \"Bithumb 8\",\n        \"tipo\": \"cex\"\n    },\n    \"0xed48dc0628789c2956b1e41726d062a86ec45bff\": {\n        \"nombre\": \"Bithumb 9\",\n        \"tipo\": \"cex\"\n    },\n    \"0x3fbe1f8fc5ddb27d428aa60f661eaaab0d2000ce\": {\n        \"nombre\": \"Bithumb: Contract 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe79eef9b9388a4ff70ed7ec5bccd5b928ebb8bd1\": {\n        \"nombre\": \"BitMart\",\n        \"tipo\": \"cex\"\n    },\n    \"0x03bdf69b1322d623836afbd27679a1c0afa067e9\": {\n        \"nombre\": \"Bitmax 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4b1a99467a284cc690e3237bc69105956816f762\": {\n        \"nombre\": \"Bitmax 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4524baa98f9a3b9dec57caae7633936ef96bd708\": {\n        \"nombre\": \"LedgerDex\",\n        \"tipo\": \"dex\"\n    },\n    \"0xc692453625023c6e03fec04158ea31ab4de2650a\": {\n        \"nombre\": \"LocalCoin Dex 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0x37c4bcaba4bcf3a605414236b8b108f160eb45a6\": {\n        \"nombre\": \"LocalCoin Dex 2\",\n        \"tipo\": \"dex\"\n    },\n    \"0x8d1c1571367a148e92d6ac83494b1bdf3b497d07\": {\n        \"nombre\": \"LocalCoin DEX 3\",\n        \"tipo\": \"dex\"\n    },\n    \"0x944644ea989ec64c2ab9ef341d383cef586a5777\": {\n        \"nombre\": \"LoopringDEX: Beta 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0x51a2b1a38ec83b56009d5e28e6222dbb56c23c22\": {\n        \"nombre\": \"nDEX Market\",\n        \"tipo\": \"dex\"\n    },\n    \"0x794e6e91555438afc3ccf1c5076a74f42133d08d\": {\n        \"nombre\": \"OasisDEX\",\n        \"tipo\": \"dex\"\n    },\n    \"0xc22d5b2951db72b44cfb8089bb8cd374a3c354ea\": {\n        \"nombre\": \"OpenRelay\",\n        \"tipo\": \"dex\"\n    },\n    \"0xd2045edc40199019e221d71c0913343f7908d0d5\": {\n        \"nombre\": \"Paradex\",\n        \"tipo\": \"dex\"\n    },\n    \"0xf92c1ad75005e6436b4ee84e88cb23ed8a290988\": {\n        \"nombre\": \"ParaSwap\",\n        \"tipo\": \"dex\"\n    },\n    \"0xa258b39954cef5cb142fd567a46cddb31a670124\": {\n        \"nombre\": \"Radar Relay\",\n        \"tipo\": \"dex\"\n    },\n    \"0x1f0d1de1558582ad6f13763f477119a1455502af\": {\n        \"nombre\": \"Saturn Network 1\",\n        \"tipo\": \"dex\"\n    },\n    \"0xaa5bbd5a177a588b9f213505ca3740b444dbd586\": {\n        \"nombre\": \"Saturn Network 2\",\n        \"tipo\": \"dex\"\n    },\n    \"0x55890b06f0877a01bb5349d93b202961f8e27a9b\": {\n        \"nombre\": \"Shark Relay\",\n        \"tipo\": \"dex\"\n    },\n    \"0x9a2d163ab40f88c625fd475e807bbc3556566f80\": {\n        \"nombre\": \"SingularX\",\n        \"tipo\": \"dex\"\n    },\n    \"0x0681e844593a051e2882ec897ecd5444efe19ff2\": {\n        \"nombre\": \"Star Bit Ex\",\n        \"tipo\": \"dex\"\n    },\n    \"0x7ee7ca6e75de79e618e88bdf80d0b1db136b22d0\": {\n        \"nombre\": \"Switcheo Exchange V2\",\n        \"tipo\": \"dex\"\n    },\n    \"0x7219612be7036d1bfa933e16ca1246008f38c5fe\": {\n        \"nombre\": \"The Ocean\",\n        \"tipo\": \"dex\"\n    },\n    \"0x1ce7ae555139c5ef5a57cc8d814a867ee6ee33d8\": {\n        \"nombre\": \"Token.Store\",\n        \"tipo\": \"dex\"\n    },\n    \"0x5e150a33ffa97a8d22f59c77ae5487b089ef62e9\": {\n        \"nombre\": \"TokenJar\",\n        \"tipo\": \"dex\"\n    },\n    \"0xdc6c91b569c98f9f6f74d90f9beff99fdaf4248b\": {\n        \"nombre\": \"Tokenlon\",\n        \"tipo\": \"dex\"\n    },\n    \"0x77208a6000691e440026bed1b178ef4661d37426\": {\n        \"nombre\": \"Totle: Primary\",\n        \"tipo\": \"dex\"\n    },\n    \"0xbd2a43799b83d9d0ff56b85d4c140bce3d1d1c6c\": {\n        \"nombre\": \"UniswapEX\",\n        \"tipo\": \"dex\"\n    },\n    \"0xd97d09f3bd931a14382ac60f156c1285a56bb51b\": {\n        \"nombre\": \"WeDEX: Beta 2\",\n        \"tipo\": \"dex\"\n    },\n    \"0x986a2fca9eda0e06fbf7839b89bfc006ee2a23dd\": {\n        \"nombre\": \"Bitmax 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x00bdb5699745f5b860228c8f939abf1b9ae374ed\": {\n        \"nombre\": \"Bitstamp 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1522900b6dafac587d499a862861c0869be6e428\": {\n        \"nombre\": \"Bitstamp 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9a9bed3eb03e386d66f8a29dc67dc29bbb1ccb72\": {\n        \"nombre\": \"Bitstamp 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x059799f2261d37b829c2850cee67b5b975432271\": {\n        \"nombre\": \"Bitstamp 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4c766def136f59f6494f0969b1355882080cf8e0\": {\n        \"nombre\": \"Bitstamp 5\",\n        \"tipo\": \"cex\"\n    },\n    \"0xc5b611f502a0dcf6c3188fd494061ae29b2baa4f\": {\n        \"nombre\": \"Bitstamp 6\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1b8a38ea02ceda9440e00c1aeba26ee2dc570423\": {\n        \"nombre\": \"BITStorage\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98\": {\n        \"nombre\": \"Bittrex 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe94b04a0fed112f3664e45adb2b8915693dd5ff3\": {\n        \"nombre\": \"Bittrex 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x66f820a414680b5bcda5eeca5dea238543f42054\": {\n        \"nombre\": \"Bittrex 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xaa90b4aae74cee41e004bc45e45a427406c4dcae\": {\n        \"nombre\": \"BitUN.io 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf8d04a720520d0bcbc722b1d21ca194aa22699f2\": {\n        \"nombre\": \"BitUN.io 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfb9f7f41319157ac5c5dccae308a63a4337ad5d9\": {\n        \"nombre\": \"Bity.com\",\n        \"tipo\": \"cex\"\n    },\n    \"0x00cdc153aa8894d08207719fe921fff964f28ba3\": {\n        \"nombre\": \"Bitzlato\",\n        \"tipo\": \"cex\"\n    },\n    \"0x007174732705604bbbf77038332dc52fd5a5000c\": {\n        \"nombre\": \"BlockTrades Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1c00d840ccaa67c494109f46e55cfeb2d8562f5c\": {\n        \"nombre\": \"BTC-Alpha Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0x73957709695e73fd175582105c44743cf0fb6f2f\": {\n        \"nombre\": \"Bw.com\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd7c866d0d536937bf9123e02f7c052446588189f\": {\n        \"nombre\": \"C2CX: Hot Wallet\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4dc98c79a52968a6c20ce9a7a08d5e8d1c2d5605\": {\n        \"nombre\": \"CamboChanger\",\n        \"tipo\": \"cex\"\n    },\n    \"0x88988d6ef12d7084e34814b9edafa01ae0d05082\": {\n        \"nombre\": \"CamboChanger 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x72bcfa6932feacd91cb2ea44b0731ed8ae04d0d3\": {\n        \"nombre\": \"Cashierest\",\n        \"tipo\": \"cex\"\n    },\n    \"0x7a56f645dcb513d0326cbaa048e9106ff6d4cd5f\": {\n        \"nombre\": \"Catex Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfd648cc72f1b4e71cbdda7a0a91fe34d32abd656\": {\n        \"nombre\": \"ChainX\",\n        \"tipo\": \"cex\"\n    },\n    \"0x96fc4553a00c117c5b0bed950dd625d1c16dc894\": {\n        \"nombre\": \"Changelly\",\n        \"tipo\": \"cex\"\n    },\n    \"0x8958618332df62af93053cb9c535e26462c959b0\": {\n        \"nombre\": \"Cobinhood 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb726da4fbdc3e4dbda97bb20998cf899b0e727e0\": {\n        \"nombre\": \"Cobinhood 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9539e0b14021a43cde41d9d45dc34969be9c7cb0\": {\n        \"nombre\": \"Coinbene\",\n        \"tipo\": \"cex\"\n    },\n    \"0x33683b94334eebc9bd3ea85ddbda4a86fb461405\": {\n        \"nombre\": \"Coinbene: Cold Wallet\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb6ba1931e4e74fd080587688f6db10e830f810d5\": {\n        \"nombre\": \"Coindelta\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb9ee1e551f538a464e8f8c41e9904498505b49b0\": {\n        \"nombre\": \"Coinex\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4b01721f0244e7c5b5f63c20942850e447f5a5ee\": {\n        \"nombre\": \"CoinExchange.io\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd4bddf5e3d0435d7a6214a0b949c7bb58621f37c\": {\n        \"nombre\": \"Coinhako\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf2d4766ad705e3a5c9ba5b0436b473085f82f82f\": {\n        \"nombre\": \"Coinhako: Warm Wallet\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa270f3ad1a7a82e6a3157f12a900f1e25bc4fbfd\": {\n        \"nombre\": \"CoinMetro Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0x167a9333bf582556f35bd4d16a7e80e191aa6476\": {\n        \"nombre\": \"Coinone 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1e2fcfd26d36183f1a5d90f0e6296915b02bcb40\": {\n        \"nombre\": \"Coinone 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd0808da05cc71a9f308d330bc9c5c81bbc26fc59\": {\n        \"nombre\": \"Coinswitch\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0d6b5a54f940bf3d52e438cab785981aaefdf40c\": {\n        \"nombre\": \"COSS.io 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd1560b3984b7481cd9a8f40435a53c860187174d\": {\n        \"nombre\": \"COSS.io 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x521db06bf657ed1d6c98553a70319a8ddbac75a3\": {\n        \"nombre\": \"CREX24\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5baeac0a0417a05733884852aa068b706967e790\": {\n        \"nombre\": \"Cryptopia 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2984581ece53a4390d1f568673cf693139c97049\": {\n        \"nombre\": \"Cryptopia 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe17ee7b3c676701c66b395a35f0df4c2276a344e\": {\n        \"nombre\": \"DigiFinex\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2101e480e22c953b37b9d0fe6551c1354fe705e6\": {\n        \"nombre\": \"DMEX\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf1c525a488a848b58b95d79da48c21ce434290f7\": {\n        \"nombre\": \"Eidoo\",\n        \"tipo\": \"cex\"\n    },\n    \"0x8d76166c22658a144c0211d87abf152e6a2d9d95\": {\n        \"nombre\": \"Eterbase\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd3808c5d48903be1490989f3fce2a2b3890e8eb6\": {\n        \"nombre\": \"Exchange A\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1fd6267f0d86f62d88172b998390afee2a1f54b6\": {\n        \"nombre\": \"Exmo 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd7b9a9b2f665849c4071ad5af77d8c76aa30fb32\": {\n        \"nombre\": \"Exmo 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x94fe3ad91dacba8ec4b82f56ff7c122181f1535d\": {\n        \"nombre\": \"Faa.st\",\n        \"tipo\": \"cex\"\n    },\n    \"0x915d7915f2b469bb654a7d903a5d4417cb8ea7df\": {\n        \"nombre\": \"FCoin\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4e5b2e1dc63f6b91cb6cd759936495434c7e972f\": {\n        \"nombre\": \"FixedFloat\",\n        \"tipo\": \"cex\"\n    },\n    \"0x91e18ee76483fa2ec5cfe2959df46673c2565be0\": {\n        \"nombre\": \"Flybit\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0021845f4c2604c58f9ba5b7bff58d16a2ab372c\": {\n        \"nombre\": \"Folgory Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2\": {\n        \"nombre\": \"FTX Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0d0707963952f2fba59dd06f2b425ace40b492fe\": {\n        \"nombre\": \"Gate.io 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x7793cd85c11a924478d358d49b05b37e91b5810f\": {\n        \"nombre\": \"Gate.io 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c\": {\n        \"nombre\": \"Gate.io 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd793281182a0e3e023116004778f45c29fc14f19\": {\n        \"nombre\": \"Gate.io: Contract 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9f5ca0012b9b72e8f3db57092a6f26bf4f13dc69\": {\n        \"nombre\": \"GBX\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd24400ae8bfebb18ca49be86258a3c749cf46853\": {\n        \"nombre\": \"Gemini 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6fc82a5fe25a5cdb58bc74600a40a69c065263f8\": {\n        \"nombre\": \"Gemini 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x61edcdf5bb737adffe5043706e7c5bb1f1a56eea\": {\n        \"nombre\": \"Gemini 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x07ee55aa48bb72dcc6e9d78256648910de513eca\": {\n        \"nombre\": \"Gemini: Contract 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9fb01a2584aac5aae3fab1ed25f86c5269b32999\": {\n        \"nombre\": \"GGBTC.com\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9c67e141c0472115aa1b98bd0088418be68fd249\": {\n        \"nombre\": \"HitBTC 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x59a5208b32e627891c389ebafc644145224006e8\": {\n        \"nombre\": \"HitBTC 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa12431d0b9db640034b0cdfceef9cce161e62be4\": {\n        \"nombre\": \"HitBTC 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x980a4732c8855ffc8112e6746bd62095b4c2228f\": {\n        \"nombre\": \"Hoo.com\",\n        \"tipo\": \"cex\"\n    },\n    \"0x274f3c32c90517975e29dfc209a23f315c1e5fc7\": {\n        \"nombre\": \"Hotbit 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x8533a0bd9310eb63e7cc8e1116c18a3d67b1976a\": {\n        \"nombre\": \"Hotbit 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xab5c66752a9e8167967685f1450532fb96d5d24f\": {\n        \"nombre\": \"Huobi 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe93381fb4c4f14bda253907b18fad305d799241a\": {\n        \"nombre\": \"Huobi 10\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfa4b5be3f2f84f56703c42eb22142744e95a2c58\": {\n        \"nombre\": \"Huobi 11\",\n        \"tipo\": \"cex\"\n    },\n    \"0x46705dfff24256421a05d056c29e81bdc09723b8\": {\n        \"nombre\": \"Huobi 12\",\n        \"tipo\": \"cex\"\n    },\n    \"0x32598293906b5b17c27d657db3ad2c9b3f3e4265\": {\n        \"nombre\": \"Huobi 13\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5861b8446a2f6e19a067874c133f04c578928727\": {\n        \"nombre\": \"Huobi 14\",\n        \"tipo\": \"cex\"\n    },\n    \"0x926fc576b7facf6ae2d08ee2d4734c134a743988\": {\n        \"nombre\": \"Huobi 15\",\n        \"tipo\": \"cex\"\n    },\n    \"0xeec606a66edb6f497662ea31b5eb1610da87ab5f\": {\n        \"nombre\": \"Huobi 16\",\n        \"tipo\": \"cex\"\n    },\n    \"0x7ef35bb398e0416b81b019fea395219b65c52164\": {\n        \"nombre\": \"Huobi 17\",\n        \"tipo\": \"cex\"\n    },\n    \"0x229b5c097f9b35009ca1321ad2034d4b3d5070f6\": {\n        \"nombre\": \"Huobi 18\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd8a83b72377476d0a66683cde20a8aad0b628713\": {\n        \"nombre\": \"Huobi 19\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b\": {\n        \"nombre\": \"Huobi 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x90e9ddd9d8d5ae4e3763d0cf856c97594dea7325\": {\n        \"nombre\": \"Huobi 20\",\n        \"tipo\": \"cex\"\n    },\n    \"0x18916e1a2933cb349145a280473a5de8eb6630cb\": {\n        \"nombre\": \"Huobi 21\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6f48a3e70f0251d1e83a989e62aaa2281a6d5380\": {\n        \"nombre\": \"Huobi 22\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf056f435ba0cc4fcd2f1b17e3766549ffc404b94\": {\n        \"nombre\": \"Huobi 23\",\n        \"tipo\": \"cex\"\n    },\n    \"0x137ad9c4777e1d36e4b605e745e8f37b2b62e9c5\": {\n        \"nombre\": \"Huobi 24\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5401dbf7da53e1c9dbf484e3d69505815f2f5e6e\": {\n        \"nombre\": \"Huobi 25\",\n        \"tipo\": \"cex\"\n    },\n    \"0x034f854b44d28e26386c1bc37ff9b20c6380b00d\": {\n        \"nombre\": \"Huobi 26\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0577a79cfc63bbc0df38833ff4c4a3bf2095b404\": {\n        \"nombre\": \"Huobi 27\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0c6c34cdd915845376fb5407e0895196c9dd4eec\": {\n        \"nombre\": \"Huobi 28\",\n        \"tipo\": \"cex\"\n    },\n    \"0x794d28ac31bcb136294761a556b68d2634094153\": {\n        \"nombre\": \"Huobi 29\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfdb16996831753d5331ff813c29a93c76834a0ad\": {\n        \"nombre\": \"Huobi 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfd54078badd5653571726c3370afb127351a6f26\": {\n        \"nombre\": \"Huobi 30\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb4cd0386d2db86f30c1a11c2b8c4f4185c1dade9\": {\n        \"nombre\": \"Huobi 31\",\n        \"tipo\": \"cex\"\n    },\n    \"0x4d77a1144dc74f26838b69391a6d3b1e403d0990\": {\n        \"nombre\": \"Huobi 32\",\n        \"tipo\": \"cex\"\n    },\n    \"0x28ffe35688ffffd0659aee2e34778b0ae4e193ad\": {\n        \"nombre\": \"Huobi 33\",\n        \"tipo\": \"cex\"\n    },\n    \"0xcac725bef4f114f728cbcfd744a731c2a463c3fc\": {\n        \"nombre\": \"Huobi 34\",\n        \"tipo\": \"cex\"\n    },\n    \"0xeee28d484628d41a82d01e21d12e2e78d69920da\": {\n        \"nombre\": \"Huobi 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5c985e89dde482efe97ea9f1950ad149eb73829b\": {\n        \"nombre\": \"Huobi 5\",\n        \"tipo\": \"cex\"\n    },\n    \"0xdc76cd25977e0a5ae17155770273ad58648900d3\": {\n        \"nombre\": \"Huobi 6\",\n        \"tipo\": \"cex\"\n    },\n    \"0xadb2b42f6bd96f5c65920b9ac88619dce4166f94\": {\n        \"nombre\": \"Huobi 7\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa8660c8ffd6d578f657b72c0c811284aef0b735e\": {\n        \"nombre\": \"Huobi 8\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1062a747393198f70f71ec65a582423dba7e5ab3\": {\n        \"nombre\": \"Huobi 9\",\n        \"tipo\": \"cex\"\n    },\n    \"0x3c11c3025ce387d76c2eddf1493ec55a8cc2a0f7\": {\n        \"nombre\": \"Idax.global\",\n        \"tipo\": \"cex\"\n    },\n    \"0x51836a753e344257b361519e948ffcaf5fb8d521\": {\n        \"nombre\": \"Indodax 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9cbadd5ce7e14742f70414a6dcbd4e7bb8712719\": {\n        \"nombre\": \"Indodax 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb1a34309af7f29b4195a6b589737f86e14597ddc\": {\n        \"nombre\": \"IndoEx LTD\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf09ff5eb57a3c8880934201c91eefbd1ace72033\": {\n        \"nombre\": \"JPMarket.cc\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2910543af39aba0cd09dbb2d50200b3e800a63d2\": {\n        \"nombre\": \"Kraken 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13\": {\n        \"nombre\": \"Kraken 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe853c56864a2ebe4576a807d26fdc4a0ada51919\": {\n        \"nombre\": \"Kraken 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0\": {\n        \"nombre\": \"Kraken 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfa52274dd61e1643d2205169732f29114bc240b3\": {\n        \"nombre\": \"Kraken 5\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe8a0e282e6a3e8023465accd47fae39dd5db010b\": {\n        \"nombre\": \"Kryptono 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x629a7144235259336ea2694167f3c8b856edd7dc\": {\n        \"nombre\": \"Kryptono 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x30b71d015f60e2f959743038ce0aaec9b4c1ea44\": {\n        \"nombre\": \"Kryptono 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2b5634c42055806a59e9107ed44d43c426e58258\": {\n        \"nombre\": \"KuCoin 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x689c56aef474df92d44a1b70850f808488f9769c\": {\n        \"nombre\": \"KuCoin 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xea81ce54a0afa10a027f65503bd52fba83d745b8\": {\n        \"nombre\": \"Kuna.io\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0861fca546225fbf8806986d211c8398f7457734\": {\n        \"nombre\": \"LAToken 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x7891b20c690605f4e370d6944c8a5dbfac5a451c\": {\n        \"nombre\": \"LAToken 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1b6c1a0e20af81b922cb454c3e52408496ee7201\": {\n        \"nombre\": \"LAToken 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x8271b2e8cbe29396e9563229030c89679b9470db\": {\n        \"nombre\": \"Liqui.io 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5e575279bf9f4acf0a130c186861454247394c06\": {\n        \"nombre\": \"Liqui.io 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xedbb72e6b3cf66a792bff7faac5ea769fe810517\": {\n        \"nombre\": \"Liquid\",\n        \"tipo\": \"cex\"\n    },\n    \"0x243bec9256c9a3469da22103891465b47583d9f1\": {\n        \"nombre\": \"Livecoin.net\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe03c23519e18d64f144d2800e30e81b0065c48b5\": {\n        \"nombre\": \"Mercatox\",\n        \"tipo\": \"cex\"\n    },\n    \"0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88\": {\n        \"nombre\": \"MXC 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0211f3cedbef3143223d3acf0e589747933e8527\": {\n        \"nombre\": \"MXC 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xae7006588d03bd15d6954e3084a7e644596bc251\": {\n        \"nombre\": \"NEXBIT Pro\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6cc5f688a315f3dc28a7781717a9a798a59fda7b\": {\n        \"nombre\": \"OKEx 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x236f9f97e0e62388479bf9e5ba4889e46b0273c3\": {\n        \"nombre\": \"OKEx 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa7efae728d2936e78bda97dc267687568dd593f3\": {\n        \"nombre\": \"OKEx 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x03e3ff995863828554282e80870b489cc31dc8bc\": {\n        \"nombre\": \"OMGFIN Exchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0xaeec6f5aca72f3a005af1b3420ab8c8c7009bac8\": {\n        \"nombre\": \"OTCBTC\",\n        \"tipo\": \"cex\"\n    },\n    \"0xbd8ef191caa1571e8ad4619ae894e07a75de0c35\": {\n        \"nombre\": \"Paribu 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2bb97b6cf6ffe53576032c11711d59bd056830ee\": {\n        \"nombre\": \"Paribu 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfb90501083a3b6af766c8da35d3dde01eb0d2a68\": {\n        \"nombre\": \"Paribu 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xabc74170f3cb8ab352820c39cc1d1e05ce9e41d3\": {\n        \"nombre\": \"Paribu 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd4dcd2459bb78d7a645aa7e196857d421b10d93f\": {\n        \"nombre\": \"Peatio\",\n        \"tipo\": \"cex\"\n    },\n    \"0x32be343b94f860124dc4fee278fdcbd38c102d88\": {\n        \"nombre\": \"Poloniex 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x209c4784ab1e8183cf58ca33cb740efbf3fc18ef\": {\n        \"nombre\": \"Poloniex 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb794f5ea0ba39494ce839613fffba74279579268\": {\n        \"nombre\": \"Poloniex 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa910f92acdaf488fa6ef02174fb86208ad7722ba\": {\n        \"nombre\": \"Poloniex 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0xaa9fa73dfe17ecaa2c89b39f0bb2779613c5fc3b\": {\n        \"nombre\": \"Poloniex: BAT\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2fa2bc2ce6a4f92952921a4caa46b3727d24a1ec\": {\n        \"nombre\": \"Poloniex: BNT\",\n        \"tipo\": \"cex\"\n    },\n    \"0x31a2feb9b5d3b5f4e76c71d6c92fc46ebb3cb1c1\": {\n        \"nombre\": \"Poloniex: CVC\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6b71834d65c5c4d8ed158d54b47e6ea4ff4e5437\": {\n        \"nombre\": \"Poloniex: FOAM\",\n        \"tipo\": \"cex\"\n    },\n    \"0x48d466b7c0d32b61e8a82cd2bcf060f7c3f966df\": {\n        \"nombre\": \"Poloniex: GNO\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0536806df512d6cdde913cf95c9886f65b1d3462\": {\n        \"nombre\": \"Poloniex: GNT\",\n        \"tipo\": \"cex\"\n    },\n    \"0x8d451ae5ee8f557a9ce7a9d7be8a8cb40002d5cb\": {\n        \"nombre\": \"Poloniex: KNC\",\n        \"tipo\": \"cex\"\n    },\n    \"0xbd2ec7c608a06fe975dbdca729e84dedb34ecc21\": {\n        \"nombre\": \"Poloniex: LOOM\",\n        \"tipo\": \"cex\"\n    },\n    \"0xc0e30823e5e628df8bc9bf2636a347e1512f0ecb\": {\n        \"nombre\": \"Poloniex: MANA\",\n        \"tipo\": \"cex\"\n    },\n    \"0x65f9b2e4d7aaeb40ffea8c6f5844d5ad7da257e0\": {\n        \"nombre\": \"Poloniex: NXC\",\n        \"tipo\": \"cex\"\n    },\n    \"0x36b01066b7fa4a0fdb2968ea0256c848e9135674\": {\n        \"nombre\": \"Poloniex: OMG\",\n        \"tipo\": \"cex\"\n    },\n    \"0xab11204cfeaccffa63c2d23aef2ea9accdb0a0d5\": {\n        \"nombre\": \"Poloniex: REP\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6795cf8eb25585eadc356ae32ac6641016c550f2\": {\n        \"nombre\": \"Poloniex: SNT\",\n        \"tipo\": \"cex\"\n    },\n    \"0xfbf2173154f7625713be22e0504404ebfe021eae\": {\n        \"nombre\": \"Poloniex: STORJ\",\n        \"tipo\": \"cex\"\n    },\n    \"0x6f803466bcd17f44fa18975bf7c509ba64bf3825\": {\n        \"nombre\": \"Poloniex: USDC\",\n        \"tipo\": \"cex\"\n    },\n    \"0xead6be34ce315940264519f250d8160f369fa5cd\": {\n        \"nombre\": \"Poloniex: ZRX\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd344539efe31f8b6de983a0cab4fb721fc69c547\": {\n        \"nombre\": \"QuantaEx 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5ca39c42f4dee3a5ba8fec3ad4902157d48700bf\": {\n        \"nombre\": \"QuantaEx 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2a048d9a8ffdd239f063b09854976c3049ae659c\": {\n        \"nombre\": \"QuantaEx 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb8cf411b956b3f9013c1d0ac8c909b086218207c\": {\n        \"nombre\": \"Remitano 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2819c144d5946404c0516b6f817a960db37d4929\": {\n        \"nombre\": \"Remitano 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x120a270bbc009644e35f0bb6ab13f95b8199c4ad\": {\n        \"nombre\": \"ShapeShift 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x9e6316f44baeeee5d41a1070516cc5fa47baf227\": {\n        \"nombre\": \"ShapeShift 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x70faa28a6b8d6829a4b1e649d26ec9a2a39ba413\": {\n        \"nombre\": \"ShapeShift 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x563b377a956c80d77a7c613a9343699ad6123911\": {\n        \"nombre\": \"ShapeShift 4\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd3273eba07248020bf98a8b560ec1576a612102f\": {\n        \"nombre\": \"ShapeShift 5\",\n        \"tipo\": \"cex\"\n    },\n    \"0x3b0bc51ab9de1e5b7b6e34e5b960285805c41736\": {\n        \"nombre\": \"ShapeShift 6\",\n        \"tipo\": \"cex\"\n    },\n    \"0xeed16856d551569d134530ee3967ec79995e2051\": {\n        \"nombre\": \"ShapeShift 7\",\n        \"tipo\": \"cex\"\n    },\n    \"0x324cc2c9fb379ea7a0d1c0862c3b48ca28d174a4\": {\n        \"nombre\": \"SouthXchange\",\n        \"tipo\": \"cex\"\n    },\n    \"0x91f6d99b232153cb655ad3e0d05e13ef505f6cd5\": {\n        \"nombre\": \"Sparrow Exchange 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xe855283086fbee485aecf2084345a91424c23954\": {\n        \"nombre\": \"Sparrow Exchange 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0xa96b536eef496e21f5432fd258b6f78cf3673f74\": {\n        \"nombre\": \"Switchain\",\n        \"tipo\": \"cex\"\n    },\n    \"0xea3a46bd1dbd0620d80037f70d0bf7c7dc5a837c\": {\n        \"nombre\": \"TAGZ 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xed8204345a0cf4639d2db61a4877128fe5cf7599\": {\n        \"nombre\": \"TAGZ 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x3613ef1125a078ef96ffc898c4ec28d73c5b8c52\": {\n        \"nombre\": \"Tidex 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0a73573cf2903d2d8305b1ecb9e9730186a312ae\": {\n        \"nombre\": \"Tidex 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x0068eb681ec52dbd9944517d785727310b494575\": {\n        \"nombre\": \"Tokocrypto\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb2cc3cdd53fc9a1aeaf3a68edeba2736238ddc5d\": {\n        \"nombre\": \"TopBTC\",\n        \"tipo\": \"cex\"\n    },\n    \"0x1119aaefb02bf12b84d28a5d8ea48ec3c90ef1db\": {\n        \"nombre\": \"Trade.io\",\n        \"tipo\": \"cex\"\n    },\n    \"0x2f1233ec3a4930fd95874291db7da9e90dfb2f03\": {\n        \"nombre\": \"Uex\",\n        \"tipo\": \"cex\"\n    },\n    \"0x390de26d772d2e2005c6d1d24afc902bae37a4bb\": {\n        \"nombre\": \"Upbit 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xba826fec90cefdf6706858e5fbafcb27a290fbe0\": {\n        \"nombre\": \"Upbit 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x5e032243d507c743b061ef021e2ec7fcc6d3ab89\": {\n        \"nombre\": \"Upbit 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0xb436c96c6de1f50a160ed307317c275424dbe4f2\": {\n        \"nombre\": \"Vinex\",\n        \"tipo\": \"cex\"\n    },\n    \"0xf5bec430576ff1b82e44ddb5a1c93f6f9d0884f3\": {\n        \"nombre\": \"Yobit.net\",\n        \"tipo\": \"cex\"\n    },\n    \"0x8f3ab2c3b651382b07a76653d2be9eb4b87e1630\": {\n        \"nombre\": \"YOOBTC 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0xd94c9ff168dc6aebf9b6cc86deff54f3fb0afc33\": {\n        \"nombre\": \"Yunbi 1\",\n        \"tipo\": \"cex\"\n    },\n    \"0x42da8a05cb7ed9a43572b5ba1b8f82a0a6e263dc\": {\n        \"nombre\": \"Yunbi 2\",\n        \"tipo\": \"cex\"\n    },\n    \"0x700f6912e5753e91ea3fae877a2374a2db1245d7\": {\n        \"nombre\": \"Yunbi 3\",\n        \"tipo\": \"cex\"\n    },\n    \"0x60d0cc2ae15859f69bf74dadb8ae3bd58434976b\": {\n        \"nombre\": \"ZB.com\",\n        \"tipo\": \"cex\"\n    }\n}\n\ngrafo.etiquetas.update(ETIQUETAS)\n\nprint(\"Etiquetas cargadas:\", len(grafo.etiquetas))\nprint(\"Ejemplo:\", grafo.nombre(\"0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be\"))\n"

portada = """
# Proyecto final — Red de transferencias de Ethereum

**Estructura de Datos — Universidad Industrial de Santander**

**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros

---

Este notebook usa **un solo dataset**:

```
transferencias.parquet
```

El profesor lo sube y el notebook hace todo lo demás:

1. Analiza las 38,9 M de transferencias con DuckDB.
2. Genera una muestra conectada de USDC.
3. Ejecuta las cuatro tareas con estructuras de datos básicas.
4. Explica la teoría y la complejidad de cada algoritmo.

| Tarea | Pregunta | Algoritmo | Responsable |
|---|---|---|---|
| 1 | ¿Cuál es el camino más barato? | Bellman-Ford | Pablo Álvarez |
| 2 | ¿Qué nodos son más importantes? | Grado + PageRank | Jhon Arciniegas |
| 3 | ¿Qué grupos de nodos hay? | Louvain | Emerson Ballesteros |
| 4 | ¿Cuál es la red mínima? | Kruskal + Union-Find | Grupal |

> **Cómo ejecutar:** sube `transferencias.parquet`, ejecuta las celdas en
> orden y listo. No necesitas clonar el repositorio ni instalar módulos.
"""

teoria_md = "## Teoría: grafos y estructuras de datos\n\nUn **grafo** tiene nodos y aristas. En este proyecto:\n\n- **Nodo**: una dirección de Ethereum.\n- **Arista**: una transferencia de una dirección a otra.\n- **Peso**: la cantidad transferida.\n\nEl grafo es **dirigido** (A → B no es lo mismo que B → A) y **ponderado**.\n\n### Estructuras de datos que usamos\n\n| Estructura | Dónde se usa | Para qué |\n|---|---|---|\n| **Lista de adyacencia** (`dict` de listas) | T1, T2, T3 | recorrer los vecinos de un nodo |\n| **Diccionario** | T1, T2, T3 | guardar distancias, puntajes y comunidades |\n| **Conjunto** (`set`) | T2, T3 | nodos visitados y comunidades vecinas |\n| **Cola** (`deque`) | T1, T3 | recorrer por niveles y encontrar componentes |\n| **Lista de aristas** | T4 | ordenar las aristas por peso |\n| **Union-Find** | T4 | detectar ciclos en Kruskal |\n\nLa idea es simple: **cada algoritmo usa la estructura que le permite hacer su trabajo sin recorrer el grafo de más**."

capa_datos_md = """
## 0. Capa de datos: el grafo

Esta celda define la estructura compartida: un grafo dirigido y ponderado.

- **Nodos**: direcciones Ethereum.
- **Aristas**: transferencias `(from_address, to_address, value)`.
- **Peso**: cantidad transferida.

El resto de celdas usan el mismo objeto `grafo`.
"""

t1_md = """
## Tarea 1 — Bellman-Ford: camino de costo mínimo

**Responsable:** Pablo Álvarez

**Estructura de datos:** lista de adyacencia + diccionario de distancias.

El costo de un camino es la suma de los pesos de sus aristas. Bellman-Ford
relaja todas las aristas `|V|-1` veces y detecta ciclos negativos.

La implementación está en la celda siguiente y se prueba con la muestra.
"""

t1_demo = '''
# ============ DEMO TAREA 1 ============
from collections import Counter

salidas = Counter(origen for origen, _, _ in grafo.aristas)
etiquetados = sorted(
    (n for n in salidas if n in grafo.etiquetas),
    key=salidas.get, reverse=True,
)
origen = etiquetados[0] if etiquetados else max(salidas, key=salidas.get)

distancias, previos = bellman_ford_desde_aristas(grafo.aristas, origen)
alcanzables = sorted(
    (d, nodo) for nodo, d in distancias.items()
    if d != float("inf") and nodo != origen
)
inalcanzables = sum(1 for d in distancias.values() if d == float("inf"))

print(f"Origen: {grafo.nombre(origen)}")
print(f"Nodos alcanzables: {len(alcanzables):,}")
print(f"Nodos inalcanzables: {inalcanzables:,}\\n")
print("Los 10 destinos más baratos:")
for d, destino in alcanzables[:10]:
    camino = reconstruir_camino(previos, origen, destino)
    nombres = " -> ".join(grafo.nombre(n) for n in camino)
    print(f"  {grafo.nombre(destino):<16} costo={d:>14,.2f}  ({nombres})")
'''

t2_md = """
## Tarea 2 — Centralidad y PageRank

**Responsable:** Jhon Arciniegas

**Estructura de datos:** lista de adyacencia + diccionario de puntajes.

- **Grado**: número de conexiones de un nodo.
- **PageRank**: importancia según quién apunta a quién.

PageRank se calcula con iteración de potencias y factor de amortiguación
`d = 0.85`.

La gráfica del top 5 y las validaciones de esta sección fueron aportadas por
Jhon Arciniegas (T2).
"""

t2_demo = '''
# ============ DEMO TAREA 2 ============
import matplotlib.pyplot as plt

cent_grado = centralidad_grado_desde_aristas(grafo.aristas)
pr = pagerank_desde_aristas(grafo.aristas)

print("Top 10 por grado:")
for _, score, nombre in top_n(cent_grado, n=10, etiquetas=grafo.etiquetas):
    print(f"  {nombre:<18} {score:.4f}")

print("\\nTop 10 por PageRank:")
for _, score, nombre in top_n(pr, n=10, etiquetas=grafo.etiquetas):
    print(f"  {nombre:<18} {score:.4f}")

# Gráfica y validaciones aportadas por Jhon Arciniegas (T2).
top_pr = top_n(pr, n=5, etiquetas=grafo.etiquetas)
nombres_pr = [nombre for _, _, nombre in top_pr]
scores_pr = [score for _, score, _ in top_pr]

plt.figure(figsize=(7, 4))
plt.barh(nombres_pr[::-1], scores_pr[::-1], color="steelblue")
plt.xlabel("PageRank")
plt.title("Top 5 direcciones por PageRank")
plt.tight_layout()
plt.show()

# Validaciones de centralidad (mismas que tests/test_centralidad.py).
assert centralidad_grado({"A": []}, {"A"})["A"] == 0.0
assert pagerank({}, set()) == {}
assert top_n({"A": 0.5, "B": 0.3}, n=2)[0][0] == "A"
print("Validaciones de centralidad: OK")
'''

t3_md = r"""
## Tarea 3 — Louvain: detección de comunidades

**Responsable:** Emerson Ballesteros

### Antes del código: ¿qué es una comunidad?

Imagina cuatro direcciones:

```
Ana   <--> Beto     (se transfieren mucho)
Carla <--> Dani     (se transfieren mucho)
Beto  -->  Carla    (se transfieren poquito)
```

Hay dos grupos naturales: `{Ana, Beto}` y `{Carla, Dani}`. Louvain intenta
encontrar esos grupos automáticamente, sin que le digamos cuántos hay.

### ¿Qué mide la modularidad Q?

Q compara las aristas que quedan **dentro** de los grupos con las que
aparecerían si las conexiones fueran al azar. Si hay más conexiones internas
de las esperadas, Q sube.

$$Q = \sum_c \left[\frac{L_c}{m} - \left(\frac{K_c}{2m}\right)^2\right]$$

- `L_c`: peso de las aristas internas de la comunidad `c`.
- `K_c`: suma de grados de los nodos de `c`.
- `m`: peso total del grafo.
- `Q > 0.3` sugiere una estructura de comunidades clara.
- `Q = 0` significa que la partición no es mejor que el azar.

### Paso a paso del algoritmo

1. Cada nodo empieza en su propia comunidad.
2. Se recorre la lista de nodos en orden aleatorio.
3. Para cada nodo, se prueba moverlo a la comunidad de cada vecino.
4. Se acepta el movimiento solo si Q aumenta.
5. Cuando una pasada completa no cambia nada, el algoritmo termina.

### Cómo leer el código

| Función | Qué hace |
|---|---|
| `simetrizar` | convierte el grafo dirigido en no dirigido |
| `calcular_grados` | suma los pesos de las aristas de cada nodo |
| `modularidad` | calcula Q de una partición |
| `louvain` | hace las pasadas y mueve los nodos |
| `desde_aristas` | construye el grafo no dirigido desde `grafo.aristas` |
| `louvain_desde_aristas` | atajo: construye el grafo y ejecuta Louvain |
| `renumerar_comunidades` | cambia los IDs por 0, 1, 2, ... para leerlos mejor |

### Qué mirar en los resultados

- Los **IDs de comunidad son arbitrarios**: la comunidad 0 no es mejor que la 5.
- Lo importante es **Q**, el **tamaño** de las comunidades y **qué exchanges**
  quedan juntos.
- Louvain es **heurístico**: dos semillas pueden dar particiones parecidas
  pero no idénticas.

### Limitaciones y posibles mejoras

- Esta versión recalcula Q completo en cada prueba: es fácil de leer, pero lenta.
- No incluye la fase de agregación de Louvain.
- Puede sufrir el límite de resolución: comunidades muy pequeñas pueden pasar
  desapercibidas.
- Mejoras: calcular ΔQ incremental, agregar la fase de agregación, probar
  varias semillas y comparar con Label Propagation o `python-louvain`.
"""

t3_demo = '''
# ============ TAREA 3: LOUVAIN ============
# Paso 1: construir el grafo no dirigido.
adj_no_dirigido = desde_aristas(grafo.aristas)

cantidad_nodos = len(adj_no_dirigido)
cantidad_aristas = 0
for vecinos in adj_no_dirigido.values():
    cantidad_aristas += len(vecinos)
cantidad_aristas = cantidad_aristas // 2

print("Grafo no dirigido:")
print(f"  nodos   : {cantidad_nodos:,}")
print(f"  aristas : {cantidad_aristas:,}")

# Paso 2: ejecutar Louvain con una semilla fija.
comunidades = louvain(adj_no_dirigido, semilla=42)

# Renumerar 0, 1, 2, ... para que sea más fácil leer los resultados.
comunidades = renumerar_comunidades(comunidades)

# Paso 3: medir la calidad de la partición.
Q = modularidad(adj_no_dirigido, comunidades)

print()
print(f"Modularidad Q = {Q:.3f}")
print(f"Número de comunidades = {len(set(comunidades.values())):,}")

# Paso 4: mostrar las comunidades más grandes.
grupos = resumen_comunidades(comunidades, grafo.etiquetas)

print()
print("Comunidades más grandes:")
for posicion, (id_comunidad, nombres) in enumerate(
    sorted(grupos.items(), key=lambda par: -len(par[1]))[:10],
    start=1,
):
    nombres_legibles = sorted(nombres, key=lambda n: (n.startswith("0x"), n))
    primeros = ", ".join(nombres_legibles[:5])
    if len(nombres) > 5:
        primeros += ", ..."
    print(f"  Comunidad {posicion:>2}: {len(nombres):>4} nodos | {primeros}")

# Paso 5: ver en qué comunidad cae cada exchange etiquetado.
print()
print("Comunidad de cada exchange etiquetado:")
for direccion, info in sorted(
    grafo.etiquetas.items(), key=lambda par: par[1]["nombre"]
):
    if direccion not in comunidades:
        continue
    id_comunidad = comunidades[direccion]
    tamano = len(grupos[id_comunidad])
    print(f"  {info['nombre']:<18} comunidad {id_comunidad:>3} ({tamano} nodos)")
'''

t3_exp_md = """
### Experimento: ¿qué pasa si cambiamos la semilla?

Louvain es un algoritmo **heurístico**: el orden en que prueba los nodos
puede cambiar el resultado. Por eso se repite con varias semillas y se mira
si Q se mantiene estable.
"""

t3_exp_code = '''
# ============ EXPERIMENTO: ESTABILIDAD CON SEMILLAS ============
import matplotlib.pyplot as plt

semillas = [1, 7, 42, 123, 2024]
resultados = []

for semilla in semillas:
    comunidades_semilla = louvain(adj_no_dirigido, semilla=semilla)
    q = modularidad(adj_no_dirigido, comunidades_semilla)
    cuantas = len(set(comunidades_semilla.values()))
    resultados.append((semilla, q, cuantas))

print(f"{'Semilla':>8} {'Q':>8} {'Comunidades':>12}")
print("-" * 32)
for semilla, q, cuantas in resultados:
    print(f"{semilla:>8} {q:>8.3f} {cuantas:>12}")

mejor = max(resultados, key=lambda fila: fila[1])
print()
print(f"Mejor semilla: {mejor[0]} con Q = {mejor[1]:.3f}")

plt.figure(figsize=(6, 4))
plt.bar(
    [str(fila[0]) for fila in resultados],
    [fila[1] for fila in resultados],
    color="seagreen",
)
plt.xlabel("Semilla")
plt.ylabel("Modularidad Q")
plt.title("Sensibilidad de Louvain a la semilla")
plt.ylim(0, 1)
plt.show()
'''

t4_md = """
## Tarea 4 — Kruskal: árbol de expansión mínima

**Responsabilidad:** grupal

**Estructura de datos:** lista de aristas + Union-Find.

Se ordenan las aristas por peso y se agregan solo si no forman un ciclo,
usando **Union-Find**. El resultado tiene `|V|-1` aristas.
"""

t4_demo = '''
# ============ DEMO TAREA 4 ============
mst, costo = kruskal_desde_aristas(grafo.aristas)
print(f"MST: {len(mst)} aristas, costo total = {costo:,.2f}\\n")
print("Primeras 20 aristas del MST:")
for a, b, w in sorted(mst, key=lambda e: e[2])[:20]:
    print(f"  {grafo.nombre(a):<18} -- {grafo.nombre(b):<18} {w:,.2f}")
'''

analisis_md = """
## Estadísticas del dataset completo

Esta sección sí usa las **38.901.039 transferencias**. DuckDB lee el Parquet
por columnas y calcula los totales sin cargar todo en RAM.
"""

analisis_code = '''
# ============ ANÁLISIS DEL DATASET COMPLETO ============
import os
import time

if not RUTA_PARQUET:
    print("Sección omitida: no encontré el Parquet completo.")
    print("Súbelo a Drive como MyDrive/ED2/transferencias.parquet.")
else:
    try:
        import duckdb
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb", "pyarrow"], check=True)
        import duckdb

    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=2")
    con.execute("SET preserve_insertion_order=false")

    t0 = time.perf_counter()
    r = con.execute(f"""
        SELECT count(*) filas,
               count(DISTINCT token_address) tokens,
               min(block_number) bmin,
               max(block_number) bmax
        FROM read_parquet('{RUTA_PARQUET}')
    """).fetchone()
    print(f"Transferencias : {r[0]:,}")
    print(f"Tokens         : {r[1]}")
    print(f"Bloques        : {r[2]:,} .. {r[3]:,}")
    print(f"Tiempo         : {time.perf_counter()-t0:.1f} s")

    print("\\nTop 10 tokens por transferencias:")
    for tok, n in con.execute(f"""
        SELECT token_address, count(*) n
        FROM read_parquet('{RUTA_PARQUET}')
        GROUP BY 1 ORDER BY n DESC LIMIT 10
    """).fetchall():
        print(f"  {tok}  {n:>10,}")

    print("\\nActividad mensual aproximada:")
    for mes, n in con.execute(f"""
        SELECT strftime(to_timestamp(epoch(TIMESTAMP '2018-10-08') + (block_number-6525201)*13.5), '%Y-%m') mes,
               count(*) n
        FROM read_parquet('{RUTA_PARQUET}')
        GROUP BY mes ORDER BY mes
    """).fetchall():
        print(f"  {mes}: {n:>10,}")
'''


benchmark_md = """
### 4.1 Benchmark de escalabilidad

Extraemos subgrafos conectados reales del Parquet y medimos cuánto tarda cada
algoritmo. Si uno se pasa de 15 segundos, se marca como *timeout*.

Esto muestra, con datos reales, por qué Bellman-Ford y Louvain no pueden
ejecutarse sobre las 38,9 M de aristas en Python puro.

> Requiere haber ejecutado antes las celdas de las tareas 1–4: allí se definen
> las funciones de los cuatro algoritmos.
"""

benchmark_code = '''
# ============ BENCHMARK DE ESCALABILIDAD ============
if RUTA_PARQUET and os.path.isfile(RUTA_PARQUET):
    import signal
    from collections import defaultdict, deque

    def subgrafo_conectado(aristas, max_aristas):
        ady = defaultdict(list)
        for i, (a, b, w) in enumerate(aristas):
            ady[a].append((b, w, i))
            ady[b].append((a, w, i))
        if not ady:
            return []
        inicio = max(ady, key=lambda n: len(ady[n]))
        visitados = {inicio}
        cola = deque([inicio])
        elegidas = set()
        while cola and len(elegidas) < max_aristas:
            u = cola.popleft()
            for v, w, i in ady[u]:
                if i in elegidas:
                    continue
                elegidas.add(i)
                if len(elegidas) >= max_aristas:
                    break
                if v not in visitados:
                    visitados.add(v)
                    cola.append(v)
        return [aristas[i] for i in sorted(elegidas)]

    def construir(aristas):
        adj = defaultdict(list)
        nodos = set()
        lista = []
        for a, b, w in aristas:
            adj[a].append((b, float(w)))
            nodos.add(a)
            nodos.add(b)
            lista.append((a, b, float(w)))
        return dict(adj), nodos, lista

    class _Timeout(Exception):
        pass

    def _handler(signum, frame):
        raise _Timeout()

    def medir(func, segundos):
        if not hasattr(signal, "SIGALRM"):
            t = time.perf_counter()
            func()
            return time.perf_counter() - t
        anterior = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, segundos)
        try:
            t = time.perf_counter()
            func()
            return time.perf_counter() - t
        except _Timeout:
            return None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, anterior)

    base = con.execute(f"""
        SELECT from_address, to_address, value
        FROM read_parquet('{RUTA_PARQUET}')
        USING SAMPLE reservoir(100000 ROWS) REPEATABLE (42)
    """).fetchall()

    tamanos = [1000, 5000, 10000, 50000, 100000]
    print(f"{'Algoritmo':<14}{'Aristas':>10}{'Nodos':>10}{'Tiempo (s)':>14}")
    for tam in tamanos:
        sub = subgrafo_conectado(base, tam)
        adj, nodos, aristas = construir(sub)
        if not nodos:
            continue
        origen = max(adj, key=lambda u: len(adj[u]))
        tareas = {
            "Bellman-Ford": lambda: bellman_ford(adj, origen),
            "PageRank": lambda: pagerank(adj, nodos),
            "Louvain": lambda: louvain(simetrizar(adj)),
            "Kruskal": lambda: kruskal(nodos, aristas_no_dirigidas(aristas)),
        }
        for nombre, func in tareas.items():
            t = medir(func, 15)
            marca = "timeout" if t is None else f"{t:.4f}"
            print(f"{nombre:<14}{len(aristas):>10,}{len(nodos):>10,}{marca:>14}")
'''

conclusiones = """
## Conclusiones

1. **Un mismo dataset admite varias preguntas.** Bellman-Ford responde
   caminos, PageRank responde importancia, Louvain responde grupos y Kruskal
   responde conectividad mínima.

2. **Las estructuras de datos importan.** La lista de adyacencia, Union-Find y
   los diccionarios hacen que los algoritmos sean simples y legibles.

3. **La escala importa.** El análisis completo usa 38,9 M de transferencias con
   DuckDB; los algoritmos en Python puro se ejecutan sobre una muestra
   conectada de USDC.

4. **La muestra no reemplaza al dataset.** El Parquet conserva las 38.901.039
   filas; la muestra es solo para que los algoritmos terminen en Colab.

5. **Todo es reproducible.** La muestra tiene semilla 42 y el pipeline está
   documentado en el repositorio.
"""

celdas = [
    md(portada),
    md(teoria_md),
    md(capa_datos_md),
    code(leer_modulo("grafo.py")),
    md(drive_md),
    code(drive_code),
    md(carga_md),
    code(carga_datos),
    md(etiquetas_md),
    code(etiquetas_code),
    md(t1_md),
    code(leer_modulo("bellman_ford.py") + "\n\n" + t1_demo),
    md(t2_md),
    code(leer_modulo("centralidad.py") + "\n\n" + t2_demo),
    md(t3_md),
    code(leer_modulo("comunidades.py") + "\n\n" + t3_demo),
    md(t3_exp_md),
    code(t3_exp_code),
    md(t4_md),
    code(leer_modulo("arbol_expansion.py") + "\n\n" + t4_demo),
    md(analisis_md),
    code(analisis_code),
    md(conclusiones),
]

nb = {
    "cells": celdas,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

SALIDA.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("Notebook escrito:", SALIDA)
print("Celdas:", len(celdas))
print("Tamaño:", SALIDA.stat().st_size, "bytes")
