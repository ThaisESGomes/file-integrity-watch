# Laboratório manual

Use uma pasta de teste. Não faça o exercício em arquivos reais do sistema.

**1. Prepare os arquivos.** Os comandos abaixo funcionam com Python no Linux, macOS e Windows:

```bash
python -c "from pathlib import Path; p=Path('lab'); p.mkdir(exist_ok=True); (p/'config.txt').write_text('mode=safe\n'); (p/'obsolete.txt').write_text('old\n')"
```

**2. Registre a referência.** Guarde o manifesto fora da pasta monitorada:

```bash
python watch.py baseline lab --manifest baseline.json
```

**3. Confira antes das mudanças.** O código de saída deve ser `0`:

```bash
python watch.py check lab --manifest baseline.json
```

**4. Faça três mudanças conhecidas:**

```bash
python -c "from pathlib import Path; p=Path('lab'); (p/'config.txt').write_text('mode=evil\n'); (p/'obsolete.txt').unlink(); (p/'new.txt').write_text('new\n')"
```

**5. Compare novamente:**

```bash
python watch.py check lab --manifest baseline.json --output report.json
```

O resultado deve listar `config.txt` em `modified`, `obsolete.txt` em `removed` e `new.txt` em `added`. O código de saída será `1`, indicando diferenças encontradas.

**6. Investigue antes de aceitar uma referência nova.** Se as mudanças forem conhecidas e aprovadas:

```bash
python watch.py baseline lab --manifest baseline.json --force
```

Isso aceita o estado atual como nova referência. Não execute automaticamente após um alerta.

