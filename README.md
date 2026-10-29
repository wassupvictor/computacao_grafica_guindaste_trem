# Trem de carga

Composicao ferroviaria com uma locomotiva principal e tres vagoes de carga
com carroceria aberta, interior livre e rodas, para que as caixas fiquem visiveis
dentro deles. O trilho reto tem 40 unidades e
atravessa a cena de uma ponta a outra da janela. Cada um dos tres vagoes para
alinhado com a estacao enquanto aguarda o carregamento manual; entre paradas, o
trem avanca o espacamento entre vagoes. A locomotiva acompanha o primeiro vagao,
que aguarda a caixa antes de o trem continuar. Depois de atravessar o trilho, a animacao
encerra o programa. O deslocamento e controlado por `delta_time`, e a rotacao
das rodas acompanha a distancia percorrida.

Um guindaste movel fica do lado oposto da estacao, com rodas, cabine, braco
telescopico e gancho interativo. Use as setas para posicionar o gancho sobre
qualquer uma das tres caixas e pressione espaco para pega-la, em qualquer ordem.
Com a caixa suspensa, mova o
guindaste ate o vagao parado e pressione espaco novamente para baixa-la. O trem
aguarda o carregamento manual antes de continuar.

## Executar

```powershell
python -m pip install -r requirements.txt
python main.py
```

O mesmo ponto de entrada tambem pode ser executado com `python -m train_scene`.

`python main.py --self-test` valida o trilho reto, o movimento independente da
taxa de quadros, a pausa e a espera pelo carregamento manual sem abrir janela.
`python main.py --smoke-test` inicializa o contexto OpenGL, compila os shaders,
cria o framebuffer de sombra e renderiza um quadro antes de sair.
`python -m unittest discover -s tests -v` executa os testes automatizados da
animacao e do carregamento.

## Organizacao

```text
main.py                 ponto de entrada compativel
train_scene/
  app.py                inicializacao, loop e autoteste
  animation.py          movimento, paradas e carga
  camera.py             camera e controles
  geometry.py           malhas e geometria estatica
  math3d.py             transformacoes e matrizes
  scene.py              recursos OpenGL e composicao/renderizacao
  settings.py           dimensoes e constantes da cena
  shaders.py            shaders GLSL
tests/
  test_animation.py     testes da logica temporal
```

## Controles

As instrucoes tambem ficam visiveis no canto superior esquerdo da janela.
- `1`: frente; `2`: atras; `3`: direita; `4`: esquerda; `5`: visao superior.
- Setas esquerda/direita: girar a lança; cima/baixo: estender/recolher.
- `Espaco`: pegar uma caixa ao alcance; com a caixa suspensa, pressionar novamente para descer e soltar.
- Para carregar um vagao, use a caixa da mesma cor; uma caixa de outra cor nao e solta dentro dele.
- A linha vermelha indica a posicao vertical de mira do gancho.
- `F11`: alternar entre modo janela e tela cheia.
- `P`: pausar/retomar sem fechar a janela; `Esc`: sair.

## Shaders, atributos e uniforms

`train_scene/shaders.py` contem o vertex shader e o fragment shader principal,
alem do par minimo usado na passagem de profundidade da luz. As malhas usam um VBO
intercalado: `aPosition` (location 0, posicao local), `aNormal` (location 1,
normal local) e `aTexCoord` (location 2, coordenadas UV). A matriz normal
transforma as normais para o espaco do mundo, inclusive sob escala nao uniforme.

No shader principal, `uModel`, `uView` e `uProjection` aplicam as transformacoes
hierarquicas, a camera e a projecao em perspectiva. `uLightSpace` projeta a cena
do ponto de vista da luz; `uLightDirection`, `uCameraPosition`, `uShininess` e
`uBaseColor` controlam a iluminacao direcional e o material. `uColorTexture` e
`uUseTexture` controlam a textura; `uShadowMap` fornece a profundidade da luz;
`uEmissive` destaca os sinais e os farois.

A textura azul/dourada do vagao e uma imagem RGBA gerada no proprio programa,
com UVs definidos por face. Nao ha imagem externa. O shadow mapping tem duas
passagens: primeiro, o depth shader grava a profundidade da cena no framebuffer
da luz; depois, o fragment shader compara a profundidade projetada de cada
fragmento com esse mapa, usando PCF 3x3 e bias para suavizar bordas e reduzir
acne. A sombra e a regiao projetada/escurecida sobre o chao; nao e o mesmo que
o sombreamento difuso/especular, que calcula a aparencia iluminada das
superficies usando as normais.

## Referencias e escopo

- Material da disciplina `Computacao Grafica - Desenhando Formas com
  preenchimento.pdf`: atributos de vertice e comunicacao entre vertex shader e
  fragment shader.
- `2026 - Computacao Grafica - Trabalhando Texturas.pdf`: uso de textura e
  coordenadas UV.
- `Visao - Computacao Grafica.pdf`, `2026 - Computacao Grafica - Aulas 05 e
  06.pdf` e `_2026 - Computacao Grafica - Aulas 07 e 08.pdf`: materiais de
  visao, transformacoes e pipeline da disciplina.
- Shadow mapping implementado conforme a abordagem solicitada na secao 6.9 do
  livro adotado; os dados bibliograficos completos do livro nao foram incluidos
  entre os arquivos fornecidos.

Os arquivos disponibilizados nao contem o codigo-fonte de um framework do
livro. Por isso, a aplicacao e autocontida em PyGame/PyOpenGL e implementa
somente as rotinas pequenas necessarias para compor as formas, enviar atributos
e uniforms e renderizar a cena. Os modelos sao composicoes proprias de cubos,
cilindros e esferas; nao foram reutilizados modelos externos.
