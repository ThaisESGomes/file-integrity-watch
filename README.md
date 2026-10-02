# File Integrity Watch

Programa em Python para verificar se os arquivos de uma pasta mudaram. Ele salva uma referência com hashes SHA-256 e, na próxima comparação, mostra quais arquivos foram adicionados, removidos ou alterados.

A comparação considera o conteúdo do arquivo, então uma alteração pode ser detectada mesmo que o tamanho continue igual.

## Como executar

Requer Python 3.11 ou superior, sem instalar bibliotecas adicionais.

```bash
git clone https://github.com/ThaisESGomes/file-integrity-watch.git
cd file-integrity-watch
python demo.py
```

A demonstração cria arquivos em uma pasta temporária, registra a referência e simula três mudanças. O resultado deve mostrar uma adição, uma remoção e uma alteração. A pasta temporária é apagada ao terminar.

Veja o [resultado de exemplo](examples/demo-result.json). Há também um [laboratório manual](docs/laboratorio.md) para fazer a comparação passo a passo.

Para verificar uma pasta existente:

```bash
python watch.py baseline lab --manifest baseline.json
python watch.py check lab --manifest baseline.json --output report.json
```

No exemplo, `lab` é a pasta que será verificada. Substitua esse nome pelo caminho da sua pasta. O arquivo `baseline.json` guarda a referência e fica fora dela; `report.json` recebe o resultado da comparação.

## Resultado

O relatório separa os arquivos em `added` (adicionados), `removed` (removidos) e `modified` (alterados). Links simbólicos e arquivos especiais não são verificados e aparecem em `skipped`.

O código de saída é `0` quando a referência foi criada ou não há diferenças nos arquivos verificados, `1` quando há diferenças e `2` quando ocorre um erro.

Para aceitar as mudanças e criar uma nova referência:

```bash
python watch.py baseline lab --manifest baseline.json --force
```

Use esse comando depois de conferir as alterações. Sem `--force`, o programa não substitui uma referência existente.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os 11 testes verificam alterações de mesmo tamanho, adições e remoções, nomes Unicode, links simbólicos, falhas de leitura e proteção contra sobrescrita. Os testes e a demonstração também são executados pelo GitHub Actions em Python 3.11, 3.12 e 3.13.

## Limitações

- Faz uma comparação por execução. Não acompanha mudanças em tempo real nem identifica quem alterou um arquivo.
- Não compara permissões, proprietário, ACLs ou diretórios vazios. Renomear um arquivo aparece como remoção e adição.
- A referência não é assinada. Quem conseguir alterar os arquivos e o manifesto pode esconder mudanças; por isso, mantenha uma cópia protegida.
- Use uma pasta estável ou um snapshot. Arquivos e pastas mudando durante a leitura podem comprometer a comparação.
- O manifesto registra caminhos e a raiz absoluta. Revise esses dados antes de compartilhar.

Licença [MIT](LICENSE).
