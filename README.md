Run Python3 main.py
Run npm run start in react folder


If you get error about "react-app-rewired", use that magic in react folder:
rm -rf node_modules && npm install -f

Create json file in DegenerateFolio/DegenerateFolio Python/portfolios with folowing structure





 server.send_message_to_all('updateAllBalances/'+allBalancesToJson(getPortfolio("Testfolio")))        <-------
 forgot to replace it with something better so use only Testfolio as name for now 

{

    "name":"Testfolio",            <------
    "description":"Im rich",
    "wallets":[

    {"Internet Computer":["529ea51c22e8d66e8302eabd9297b100fdb369109822248bb86939a671fbc55b"]},
    {"Solana":["8g4Z9d6PqGkgH31tMW6FwxGhwYJrXpxZHQrkikpLJKrG"]},
    {"Ethereum":["0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97"]},
    {"Sui":["0xe9dfdf59527ef04168dc867e933a36d563b96b942541ed6c1cb4cce1e96226fe"]},
    {"NEAR Protocol":["249e1bec4d782ec1959a927ef468fcea4e1a4c29ac7e11b51a5f15bad85aecc3"]},
    {"Polkadot":["147WS8AEnEydqtJgrnfvthyPYm11imePyqwCRp4UGCFMdbH1"]},
    {"Aptos":["0x2d91309b5b07a8be428ccd75d0443e81542ffcd059d0ab380cefc552229b1a"]},
    {"Manta Network":["dfXAMGNLEvDoFv7zeGJ8jS7ubU4XDVvuGUBHgms92c8NpZeQv"]},
    {"Starknet":["0x039e67f782da34e09fc8483eb8820cf8036e622639c6823d1d1cc349192d93cf"]},
    {"Cosmos":["cosmos1numazl76nnrzqxehythk7cj8e249gjlc5p5rde"]},
    {"Sei":["sei18qgau4n88tdaxu9y2t2y2px29yvwp50mk4xctp7grwfj7fkcdn8qvs9ry8"]},
    {"Celestia":["celestia1n52v50kwgcgr7x88vtnyk2zwweuvalfjmk5q8u"]},
    {"Algorand":["5SFNTQF5WA7GWS5RQEDZRNQ22GTAPBTLGIQDOBKOSWVT7YOOVKHVMC4Q4U"]}

    ],
    "staked": [{"CYBER":57}],
    "locked": [{"DOT":100},{"CATCH":1952},{"ENA":990}],
    "lended": [{"SUI":924},{"STRK":1288},{"FIL":205}]
}

    "staked", "locked", "lended" are for tokens that are not displayed in explorer and you dont wanna parse them somewhere else


