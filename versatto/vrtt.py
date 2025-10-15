from flask import Flask, render_template_string, request, session, jsonify, url_for
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = "supersecret"  # Troque em produção

# ===================== CONFIGURAÇÕES DE PREÇOS =====================
precos = {"MDF Branco": 1050, "MDF Amadeirado": 1150, "MDF Laca": 1250}
precos_painel = {
    "Branco": {"Comum": 500, "Ripado": 560},
    "Laca": {"Comum": 640, "Ripado": 710},
    "Amadeirado": {"Comum": 560, "Ripado": 660}
}
tipos_moveis = ["Painel", "Guarda-Roupa", "Armário de Cozinha"]

# ===================== ABRIR NAVEGADOR AUTOMATICAMENTE =====================
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# ===================== HTML PRINCIPAL =====================
HTML_ORCAMENTO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Orçamento de Móveis Planejados</title>
<style>
body { font-family: Arial; background: #f4f4f9; display: flex; justify-content: center; margin-top: 30px; }
.container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 480px; }
img.logo { display: block; margin: 0 auto 20px; max-width: 150px; }
h2 { text-align: center; color: #333; }
label { font-weight: bold; display: block; margin-top: 10px; }
input, select { width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; }
button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 6px; margin-top: 12px; cursor: pointer; font-size: 16px; }
button.secondary { background:#6c757d; }
.resultado { text-align: center; margin-top: 20px; font-size: 17px; color: #333; }
.valor-final { color: green; font-size: 19px; font-weight: bold; margin-top: 8px; }
.checkbox { margin-top: 10px; display: flex; align-items: center; }
.checkbox label { margin-left: 8px; font-weight: normal; }
.small { font-size: 13px; color: #666; margin-top:8px;}
</style>
<script>
function atualizarCampos() {
    var tipo = document.getElementById("tipo_movel").value;
    var campoPainel = document.getElementById("painel_extra");
    campoPainel.style.display = (tipo === "Painel") ? "block" : "none";
}
</script>
</head>
<body>
<div class="container">
<h2>Orçamento de Móveis Planejados</h2>

<form method="POST">
    <label>Tipo de Móvel:</label>
    <select name="tipo_movel" id="tipo_movel" onchange="atualizarCampos()" required>
        <option value="">Selecione</option>
        {% for tipo in tipos %}
            <option value="{{tipo}}">{{tipo}}</option>
        {% endfor %}
    </select>

    <div id="painel_extra" style="display:none;">
        <label>Tipo de Painel:</label>
        <select name="tipo_painel">
            <option value="Comum">Comum</option>
            <option value="Ripado">Ripado</option>
        </select>
    </div>

    <label>Altura (m):</label>
    <input type="number" step="0.01" name="altura" required>

    <label>Largura (m):</label>
    <input type="number" step="0.01" name="largura" required>

    <label>Material:</label>
    <select name="material" required>
        <option value="">Selecione</option>
        <option value="Branco">Branco</option>
        <option value="Laca">Laca</option>
        <option value="Amadeirado">Amadeirado</option>
        <option value="MDF Amadeirado">MDF Amadeirado</option>
    </select>

    <div class="checkbox">
        <input type="checkbox" name="desconto" value="sim" id="desconto">
        <label for="desconto">Aplicar desconto de 5%</label>
    </div>

    <button type="submit">Calcular Orçamento</button>
</form>

<form action="{{ url_for('design2d') }}">
    <button type="submit" class="secondary">Montar Vista Frontal 2D</button>
</form>

{% if resultado %}
<div class="resultado">
    {{ resultado|safe }}
    <div class="small">Se você salvou uma configuração 2D, ela é usada como referência visual (salva na sessão).</div>
</div>
{% endif %}
</div>
</body>
</html>
"""

# ===================== HTML DESIGN 2D =====================
HTML_2D = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Montagem 2D - Painel</title>
<style>
body { font-family: Arial; background: #f4f4f9; display: flex; flex-direction: column; align-items: center; }
canvas { background: white; border: 1px solid #ccc; margin-top: 20px; border-radius: 8px; }
.controls { margin-top: 20px; display: flex; gap: 10px; }
button { padding: 10px 15px; border-radius: 6px; border: none; cursor: pointer; font-size: 15px; }
button.save { background: #007bff; color: white; }
button.load { background: #28a745; color: white; }
button.back { background: #6c757d; color: white; }
</style>
</head>
<body>
<h2>Montagem 2D - Painel</h2>
<canvas id="canvas" width="600" height="400"></canvas>
<div class="controls">
    <button class="save" onclick="saveDesign()">Salvar Design</button>
    <button class="load" onclick="loadDesign()">Carregar Design</button>
    <form action="/" style="display:inline;"><button class="back">Voltar</button></form>
</div>

<script>
let canvas = document.getElementById("canvas");
let ctx = canvas.getContext("2d");
let elementos = [];
let selecionado = null;

canvas.addEventListener("mousedown", (e) => {
    let x = e.offsetX, y = e.offsetY;
    selecionado = null;
    for (let el of elementos) {
        if (x > el.x && x < el.x + el.w && y > el.y && y < el.y + el.h) {
            selecionado = el;
        }
    }
});

canvas.addEventListener("mousemove", (e) => {
    if (selecionado) {
        selecionado.x = e.offsetX - selecionado.w / 2;
        selecionado.y = e.offsetY - selecionado.h / 2;
        desenhar();
    }
});

canvas.addEventListener("mouseup", () => selecionado = null);

function desenhar() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    for (let el of elementos) {
        ctx.fillStyle = el.cor;
        ctx.fillRect(el.x, el.y, el.w, el.h);
        ctx.strokeRect(el.x, el.y, el.w, el.h);
    }
}

function saveDesign() {
    fetch('/save_design', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(elementos)
    }).then(r => r.json()).then(() => alert("Design salvo!"));
}

function loadDesign() {
    fetch('/load_design').then(r=>r.json()).then(d=>{
        if (d.design) {
            elementos = d.design;
            desenhar();
        } else alert("Nenhum design salvo.");
    });
}

// Inicializa com alguns módulos
elementos = [
    {x:100, y:150, w:100, h:50, cor:"#f1c40f"},
    {x:220, y:150, w:100, h:50, cor:"#3498db"}
];
desenhar();
</script>
</body>
</html>
"""

# ===================== ROTAS =====================
@app.route("/", methods=["GET","POST"])
def home():
    resultado = None
    if request.method == "POST":
        try:
            tipo_movel = request.form["tipo_movel"]
            tipo_painel = request.form.get("tipo_painel", "Comum")
            altura = float(request.form["altura"])
            largura = float(request.form["largura"])
            material = request.form["material"]
            aplicar_desconto = "desconto" in request.form

            altura_calculada = max(altura, 1.0)

            if tipo_movel == "Painel":
                if material in precos_painel:
                    preco_m2 = precos_painel[material][tipo_painel]
                else:
                    resultado = "<span style='color:red'>Painel só disponível em Branco, Laca ou Amadeirado.</span>"
                    return render_template_string(HTML_ORCAMENTO, tipos=tipos_moveis, resultado=resultado)
            else:
                if material in precos:
                    preco_m2 = precos[material]
                else:
                    resultado = "<span style='color:red'>Material inválido.</span>"
                    return render_template_string(HTML_ORCAMENTO, tipos=tipos_moveis, resultado=resultado)

            area = altura_calculada * largura
            custo_original = area * preco_m2

            if aplicar_desconto:
                custo_com_desconto = custo_original * 0.95
                resultado = (
                    f"<h3>{tipo_movel} ({tipo_painel if tipo_movel=='Painel' else ''})</h3>"
                    f"<p>Material: <b>{material}</b></p>"
                    f"<p>Altura: {altura_calculada:.2f} m</p>"
                    f"<p>Largura: {largura:.2f} m</p>"
                    f"<p>Valor por m²: R$ {preco_m2:,.2f}</p>"
                    f"Valor original: <b>R$ {custo_original:,.2f}</b><br>"
                    f"Desconto 5%<div class='valor-final'>R$ {custo_com_desconto:,.2f}</div>"
                )
            else:
                resultado = (
                    f"<h3>{tipo_movel} ({tipo_painel if tipo_movel=='Painel' else ''})</h3>"
                    f"<p>Material: <b>{material}</b></p>"
                    f"<p>Altura: {altura_calculada:.2f} m</p>"
                    f"<p>Largura: {largura:.2f} m</p>"
                    f"<p>Valor por m²: R$ {preco_m2:,.2f}</p>"
                    f"<div class='valor-final'>R$ {custo_original:,.2f}</div>"
                )
        except Exception as e:
            resultado = f"<span style='color:red'>Erro: {e}</span>"

    return render_template_string(HTML_ORCAMENTO, tipos=tipos_moveis, resultado=resultado)

@app.route("/design2d")
def design2d():
    return render_template_string(HTML_2D)

@app.route("/save_design", methods=["POST"])
def save_design():
    data = request.get_json()
    session['design'] = data
    return jsonify({"status":"ok", "saved": True, "design": data})

@app.route("/load_design")
def load_design():
    data = session.get('design')
    if data:
        return jsonify({"status":"ok", "design": data})
    return jsonify({"status":"empty", "design": None})

# ===================== EXECUÇÃO PRINCIPAL =====================
if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)