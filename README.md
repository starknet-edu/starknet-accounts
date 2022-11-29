<div align="center">
    <img src="./misc/abstract.jpg" style="width: 350px">
    <h1>Abstracción de Cuentas Starknet</h1>
    <br>
</div>

¡Bienvenidos! Este es un taller automatizado que explicará qué es [abstracción de cuenta](https://perama-v.github.io/cairo/account-abstraction) y cómo puede aprovecharlo para crear poderosos contratos de cuentas personalizados.

## Introducción

# USTED ESTÁ EN LA RAMA DE RESPUESTAS - POR FAVOR COMPRUEBE `start-here`

### Descargo de responsabilidad

​No espere ningún tipo de beneficio al usar esto, aparte de aprender un montón de cosas interesantes sobre StarkNet, el primer paquete acumulativo de validez de propósito general en Ethereum Mainnnet.
​
StarkNet todavía está en Alfa. Esto significa que el desarrollo está en curso y que la pintura no está seca en todas partes. Las cosas mejorarán, y mientras tanto, ¡hacemos que las cosas funcionen con un poco de cinta adhesiva aquí y allá!
​

### Cómo funciona

TL; DR: las cuentas en StarkNet son simplemente contratos inteligentes regulares. Una advertencia es que DEBEN tener un punto de entrada canónico indicado con los selectores:

- `__validate__`
- `__validate_declare__`
- `__execute__`

Su objetivo es diseñar contratos de cuenta que pasen todas las comprobaciones de [evaluator.cairo](contracts/evaluator.cairo) y acumulen todos los puntos disponibles en StarkNet(Goerli).

Este tutorial consta de varios "contratos de cuenta" de StarkNet y scripts auxiliares de "starknet_py" para compilación, implementación y prueba. También incluye un contrato inteligente evaluador, que comprobará que el código que escribes en el contrato de tu cuenta es correcto.

Para comprender lo que se espera de usted, ejecute el script de python especificado para cada ejercicio y lea la `declaración de misión` que aparecerá en su terminal. Los ejercicios se volverán más difíciles y requerirán que:

- Manipular los archivos de python
- Escribir el código Cairo correspondiente.

Estas tareas se anotarán con el comentario `# ELEMENTO DE ACCIÓN <NUM>`

### ¿Dónde estoy?

Este taller es el sexto de una serie destinada a enseñar cómo construir en StarkNet. Echa un vistazo a lo siguiente:

| Tema                                           | GitHub repo                                                                            |
| ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| Aprenda a leer el código de El Cairo           | [Cairo 101](https://github.com/starknet-edu/starknet-cairo-101)                        |
| Implemente y personalice un ERC721 NFT         | [StarkNet ERC721](https://github.com/starknet-edu/starknet-erc721)                     |
| Implemente y personalice un token ERC20        | [StarkNet ERC20](https://github.com/starknet-edu/starknet-erc20)                       |
| Cree una app de capa cruzada                   | [StarkNet messaging bridge](https://github.com/starknet-edu/starknet-messaging-bridge) |
| Depure sus contratos de El Cairo fácilmente    | [StarkNet debug](https://github.com/starknet-edu/starknet-debug)                       |
| Diseña tu propio contrato de cuenta            | [StarkNet account abstraction](https://github.com/starknet-edu/starknet-accounts)(usted está aquí) |


### Proporcionar comentarios y obtener ayuda

Una vez que haya terminado de trabajar en este tutorial, ¡sus comentarios serán muy apreciados!

**Complete [este formulario](https://forms.reform.app/starkware/untitled-form-4/kaes2e) para informarnos qué podemos hacer para mejorarlo.**
​
Y si tiene dificultades para seguir adelante, ¡háganoslo saber! Este taller está destinado a ser lo más accesible posible; queremos saber si no es el caso.

¿Tienes una pregunta? Únase a nuestro [servidor Discord](https://starknet.io/discord), regístrese y únase al canal #tutorials-support
​
¿Está interesado en seguir talleres en línea sobre cómo desarrollar en StarkNet? [Suscríbase aquí](http://eepurl.com/hFnpQ5)

### Contribuyendo

Este proyecto se puede mejorar y evolucionará a medida que StarkNet madure. ¡Sus contribuciones son bienvenidas! Aquí hay cosas que puede hacer para ayudar:

- Crea una sucursal con una traducción a tu idioma
- Corrija los errores si encuentra alguno.
- Agregue una explicación en los comentarios del ejercicio si cree que necesita más explicación
- Agregue ejercicios que muestren su característica favorita de El Cairo

## Preparándose para trabajar

### Paso 1: clonar el repositorio

* Oficial

```bash
git clone https://github.com/starknet-edu/starknet-accounts
cd starknet-accounts
```

* Nadai con Soluciones

```bash
gh repo clone Nadai2010/Nadai-Starknet-Edu-Accounts
cd Nadai-Starknet-Edu-Accounts
```

### Paso 2: configure su entorno

Este tutorial utiliza el [entorno cairo](https://www.cairo-lang.org/docs/quickstart.html), [starknet-devnet](https://github.com/Shard-Labs/starknet-devnet) y [starknet.py](https://github.com/software-mansion/starknet.py).

***Instalar el entorno de el cairo***

Configure el entorno siguiendo [estas instrucciones](https://starknet.io/docs/quickstart.html#quickstart)

***Instalar dependencias***

```bash
pip3 install --upgrade -r requirements.txt
```

### Paso 3: configure su red de desarrollo

Las transacciones tardan en completarse en [testnet](https://goerli.voyager.online), por lo que primero debe desarrollar y depurar localmente.

Probemos con el ejercicio `hello/hello.cairo`. No hay `# ELEMENTOS DE ACCIÓN` que deban completarse para este ejercicio y simplemente podemos probar que funciona.


#### 1) Iniciar devnet

```bash
starknet-devnet
```

#### 2) Ejecutar `deploy` evaluator

```bash
# NOTA:
# - no tiene que implementar el validador para `testnet`
# - Los detalles del contrato de devnet se pueden encontrar en `contracts/accounts.json`
cd contracts
python3 tutorial/evaluator.py
```

#### 3) Deploy/test el contrato hello

```bash
python3 hello/hello.py
```

Las direcciones de contrato del evaluador relevantes se guardan en la memoria caché `contracts/accounts.json`. Para las pruebas de devnet, los contratos de devnet `DEBEN SER ELIMINADOS` cada vez que se reinicia devnet. Si desea deshabilitar esta ejecución de caché de contrato:

```bash
export ACCOUNT_CACHE=false
```

No hubo `elementos de acción` que deba completar, por lo que debería ver una respuesta exitosa de `¡DÍA DE PAGO!` del contrato del evaluador de devnet.


### Paso 4: implementación en testnet

Al implementar en testnet, complete los detalles relevantes en el archivo `config.json` en `TESTNET_ACCOUNT` para que su cuenta de StarkNet transfiera tarifas y reciba recompensas.

#### [Argent-X](https://chrome.google.com/webstore/detail/argent-x/dlcobpjiigpikoobohmabehhmhfoodbb) Example

<div align="center">
    <img src="./misc/argent.png" style="width: 350px">
</div>

***DIRECCIÓN***

- Desde la billetera de ejemplo anterior, puede copiar la dirección (`0x0742B5662...6476f8f`)
- Pegue la representación felt en `config.json` `TESTNET_ACCOUNT` -> `ADDRESS`
- Para obtener la representación felt, puede pegar la dirección en esta [herramienta de conversión](https://util.turbofish.co).

***PRIVADO***

- Seleccione los tres puntos verticales para mostrar las opciones de billetera
- Seleccione `Exportar clave privada`
- Copie la clave privada de esta pantalla y péguela en `config.json` `TESTNET_ACCOUNT` -> `PRIVATE`.

***PÚBLICO***

- Seleccione los tres puntos verticales para mostrar las opciones de billetera
- Seleccione `Ver en Voyager`
- Desde Voyager Block Explorer, seleccione la pestaña `LEER contrato` -> `IMPLEMENTACIÓN`
- Despliega el selector `get_signer`
- Seleccione la consulta `Decimal`
- Copie la clave pública de esta pantalla y péguela en `config.json` `TESNET_ACCOUNT` -> `PUBLIC`

***Example `config.json`***
<div align="center">
    <img src="./misc/hints.png" style="width: 350px">
</div>

### Paso 5 - Contabilización de tarifas

Las cuentas en StarkNet deben pagar [tarifas](https://docs.starknet.io/docs/Fees/fee-mechanism) para cubrir la huella L1 de su transacción. Por lo tanto, los detalles de la cuenta que ingrese deben tener Goerli ETH (~ 0.5 ETH) y se pueden financiar a través de [starkgate bridge](https://goerli.starkgate.starknet.io) o [StarkNet Faucet](https://faucet.goerli.starknet.io).

Después de haber probado su contrato localmente, puede probar en `testnet` pasando el indicador `--testnet` starknet_py script:

```bash
python3 hello/hello.py --testnet
```

### Paso 6 - Usando `respuestas`

Si necesita sugerencias sobre soluciones de tutoriales, puede encontrarlas en la rama `respuestas`. Estos incluirán un pytest para que lo ejecute, el starknet_py completo y el contrato cairo completo.

## Trabajando en el tutorial

### Ejercicio 1 - [Hello](./contracts/hello)

Implementemos y probemos el contrato de cuenta más simple que podamos, [`hello.cairo`](contracts/hello/hello.cairo):

```bash
cd contracts
python3 hello/hello.py
```

El trabajo de un contrato de cuenta es ejecutar una lógica comercial arbitraria en nombre de una entidad específica. Esta es la razón por la que vemos un patrón de argumento similar para la mayoría de [ejecutar funciones](contracts/hello/hello.cairo#L11).

Siga las indicaciones y acumule 100 puntos.

### Ejercicio 2 - [Signatures](./contracts/signatures)

#### Firma 1

A diferencia de Ethereum [EOA](https://ethereum.org/en/developers/docs/accounts/#externally-owned-accounts-and-key-pairs), las cuentas de StarkNet no tienen un requisito estricto de ser administradas por un par de claves pública/privada.

La abstracción de cuenta se preocupa más por `quién` (es decir, la dirección del contrato) que por `cómo` (es decir, la firma).

Esto deja el esquema de firma ECDSA en manos del desarrollador y normalmente se implementa mediante el [pedersen hash](https://docs.starknet.io/docs/Hashing/hash-functions) y la curva nativa de Stark:

```bash
cd contracts
python3 signature/signature_1.py
```

El contrato `signature_1` no tiene el concepto de un par de claves pública/privada. Toda la firma se realizó `fuera de la cadena` y, sin embargo, con la abstracción de la cuenta, todavía podemos operar una cuenta en funcionamiento con un campo de firma completo.

Siga las indicaciones y acumule 100 puntos.

#### Firma 2 - 200 pts

Combinemos la lógica de firma de manera más sucinta con la cuenta:

***HINT: we have not yet implemented a [nonce](https://ethereum.org/en/developers/docs/accounts/#an-account-examined)***

```bash
cd contracts
python3 signature/signature_2.py
```

Aunque somos libres de completar el campo de la firma como queramos, StarkNet OS tiene un método específico para cifrar [datos de transacciones](https://docs.starknet.io/docs/Blocks/transactions#transaction-hash-1).

Siga las indicaciones y acumule 200 puntos.

#### Firma 3 - 300 pts

Como las cuentas de StarkNet son simplemente contratos, podemos implementar cualquier mecanismo de firma que queramos. Compañías como [Web3Auth](https://medium.com/toruslabs/sign-in-with-starkware-711d48f2dbbd) están usando esto para crear arquitecturas de `Inicio de sesión` usando su cuenta de StarkNet. [JWT](https://github.com/BoBowchan/cairo-jsonwebtoken) se están implementando esquemas de tokens.

Las discusiones sobre arquitecturas de cuentas novedosas están apareciendo cada vez más (https://vitalik.ca/general/2022/01/26/soulbound.html) y parece ser una herramienta cada vez más importante en el kit de herramientas del desarrollador.

Para un ejemplo de una arquitectura de cuenta única, construiremos un contrato que implemente su esquema de firmas con la curva `secp256k1` y `sha256` en lugar de nuestra curva StarkNet nativa:

```bash
cd contracts
python3 signature/signature_3.py
```

Siga las indicaciones y acumule 300 puntos.

### Ejercicio 3 - [MultiCall](./contracts/multicall)

Ahora que hemos implementado los mecanismos de firma de ECDSA vanilla, ¡veamos qué puede hacer realmente la abstracción de cuentas!

Una `multillamada` agrega los resultados de múltiples llamadas de contrato. Esto reduce la cantidad de solicitudes separadas de API Client o JSON-RPC que deben enviarse. Además, actúa como una invocación `atómica` donde se devuelven todos los valores para el mismo bloque.

Los proveedores de billeteras populares como Argent usan este diseño para implementar [contratos de cuenta](https://github.com/argentlabs/argent-contracts-starknet/blob/develop/contracts/ArgentAccount.cairo) en StarkNet para acomodar una multillamada o una sola llamar con un esquema.

Hay muchas implementaciones de multillamadas que permiten a la persona que llama flexibilidad en la forma en que distribuyen y agrupan sus transacciones.

Implementemos una cuenta multillamada para StarkNet:

```bash
cd contracts
python3 multicall/multicall.py
```

Siga las indicaciones y acumule 500 puntos.

### Ejercicio 4 - [MultiSig](./contracts/multisig)

Una billetera `multisig` o de múltiples firmas le permite compartir la seguridad entre múltiples entidades firmantes. Puede pensar en ellos como bóvedas de banco en el sentido de que requieren más de una llave para desbloquear o, en este caso, autorizar una transacción.

La cantidad de claves de firma que pertenecen a la cuenta y la cantidad de claves requeridas para autorizar una transacción son puramente detalles de implementación.

Implementemos una cuenta `2/3 multisig` (es decir, se requieren 2 firmas de un total de 3 firmantes para que se ejecute una transacción):

```bash
cd contracts
python3 multisig/multisig.py
```

Siga las indicaciones y acumule 1000 puntos.
