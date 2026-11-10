import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tarefas  # noqa: E402


class BaseCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.dir.name) / "tasks.json"
        os.environ["TAREFAS_FILE"] = str(self.arquivo)

    def tearDown(self):
        os.environ.pop("TAREFAS_FILE", None)
        self.dir.cleanup()

    def rodar(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                codigo = tarefas.main(list(argv))
            except SystemExit as e:  # argparse
                codigo = e.code
        return codigo, out.getvalue(), err.getvalue()

    def dados(self):
        return json.loads(self.arquivo.read_text(encoding="utf-8"))


class TestAdd(BaseCli):
    def test_cria_arquivo_e_tarefa(self):
        codigo, out, _ = self.rodar("add", "Estudar Python", "--prioridade", "alta")
        self.assertEqual(codigo, 0)
        self.assertIn("#1", out)
        t = self.dados()["tarefas"][0]
        self.assertEqual((t["descricao"], t["prioridade"], t["status"]),
                         ("Estudar Python", "alta", "pendente"))

    def test_ids_nao_sao_reaproveitados(self):
        self.rodar("add", "a")
        self.rodar("add", "b")
        self.rodar("remove", "2")
        self.rodar("add", "c")
        self.assertEqual([t["id"] for t in self.dados()["tarefas"]], [1, 3])

    def test_acentos_preservados(self):
        self.rodar("add", "Ação é coração")
        self.assertIn("Ação é coração", self.arquivo.read_text(encoding="utf-8"))

    def test_descricao_vazia(self):
        codigo, _, err = self.rodar("add", "   ")
        self.assertEqual(codigo, 1)
        self.assertIn("vazia", err)

    def test_data_invalida(self):
        codigo, _, err = self.rodar("add", "x", "-d", "31/12/2026")
        self.assertEqual(codigo, 1)
        self.assertIn("AAAA-MM-DD", err)
        self.assertFalse(self.arquivo.exists())

    def test_prioridade_invalida(self):
        codigo, _, _ = self.rodar("add", "x", "-p", "urgente")
        self.assertNotEqual(codigo, 0)


class TestList(BaseCli):
    def test_vazio(self):
        codigo, out, _ = self.rodar("list")
        self.assertEqual(codigo, 0)
        self.assertIn("Nenhuma tarefa", out)

    def test_ordenacao_e_filtros(self):
        self.rodar("add", "baixa tarefa", "-p", "baixa")
        self.rodar("add", "alta tarefa", "-p", "alta")
        self.rodar("add", "feita", "-p", "alta")
        self.rodar("done", "3")
        _, out, _ = self.rodar("list")
        pos = [out.index(s) for s in ("alta tarefa", "baixa tarefa", "feita")]
        self.assertEqual(pos, sorted(pos))
        _, out, _ = self.rodar("list", "--status", "concluida")
        self.assertIn("feita", out)
        self.assertNotIn("alta tarefa", out)
        _, out, _ = self.rodar("list", "--prioridade", "baixa")
        self.assertIn("baixa tarefa", out)
        self.assertNotIn("feita", out)


class TestDoneRemoveEdit(BaseCli):
    def test_done(self):
        self.rodar("add", "x")
        codigo, _, _ = self.rodar("done", "1")
        self.assertEqual(codigo, 0)
        self.assertEqual(self.dados()["tarefas"][0]["status"], "concluida")
        codigo, _, err = self.rodar("done", "1")
        self.assertEqual(codigo, 1)
        self.assertIn("já está concluída", err)

    def test_remove(self):
        self.rodar("add", "x")
        self.assertEqual(self.rodar("remove", "1")[0], 0)
        self.assertEqual(self.dados()["tarefas"], [])

    def test_id_inexistente(self):
        for cmd in (["done", "9"], ["remove", "9"], ["edit", "9", "--descricao", "x"]):
            codigo, _, err = self.rodar(*cmd)
            self.assertEqual(codigo, 1)
            self.assertIn("não encontrada", err)

    def test_edit(self):
        self.rodar("add", "x", "-d", "2026-01-01")
        self.rodar("edit", "1", "--descricao", "novo", "-p", "baixa", "-d", "2027-02-03")
        t = self.dados()["tarefas"][0]
        self.assertEqual((t["descricao"], t["prioridade"], t["data_limite"]),
                         ("novo", "baixa", "2027-02-03"))
        self.rodar("edit", "1", "--sem-data")
        self.assertIsNone(self.dados()["tarefas"][0]["data_limite"])

    def test_edit_sem_campos_ou_invalido_nao_altera(self):
        self.rodar("add", "x")
        self.assertEqual(self.rodar("edit", "1")[0], 1)
        self.assertEqual(self.rodar("edit", "1", "--descricao", "novo", "-d", "ruim")[0], 1)
        self.assertEqual(self.dados()["tarefas"][0]["descricao"], "x")


class TestArquivo(BaseCli):
    def test_json_corrompido(self):
        self.arquivo.write_text("{quebrado", encoding="utf-8")
        codigo, _, err = self.rodar("list")
        self.assertEqual(codigo, 1)
        self.assertIn("corrompido", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(self.arquivo.read_text(encoding="utf-8"), "{quebrado")

    def test_arquivo_vazio(self):
        self.arquivo.write_text("", encoding="utf-8")
        self.assertEqual(self.rodar("add", "x")[0], 0)
        self.assertEqual(len(self.dados()["tarefas"]), 1)

    def test_formato_inesperado(self):
        self.arquivo.write_text("[1, 2]", encoding="utf-8")
        codigo, _, err = self.rodar("list")
        self.assertEqual(codigo, 1)
        self.assertIn("formato", err)

    def _escrever(self, tarefas, proximo_id=10):
        self.arquivo.write_text(
            json.dumps({"proximo_id": proximo_id, "tarefas": tarefas}), encoding="utf-8")

    def test_tarefa_malformada_nao_gera_traceback(self):
        self._escrever([{"id": 1}])
        codigo, _, err = self.rodar("list")
        self.assertEqual(codigo, 1)
        self.assertIn("formato", err)
        self.assertNotIn("Traceback", err)

    def test_tarefa_sem_data_limite_e_rejeitada_sem_traceback(self):
        tarefa = {"id": 1, "descricao": "Estudar", "status": "pendente",
                  "prioridade": "alta", "criada_em": "2026-01-01T00:00:00"}
        self._escrever([tarefa], proximo_id=2)
        codigo, _, err = self.rodar("list")
        self.assertEqual(codigo, 1)
        self.assertIn("formato", err)
        self.assertNotIn("Traceback", err)

    def test_ids_duplicados_ou_proximo_id_baixo(self):
        base = {"descricao": "x", "status": "pendente", "prioridade": "media",
                "criada_em": "2026-01-01T00:00:00", "data_limite": None}
        self._escrever([{**base, "id": 1}, {**base, "id": 1}])
        self.assertEqual(self.rodar("list")[0], 1)
        self._escrever([{**base, "id": 5}], proximo_id=5)
        self.assertEqual(self.rodar("add", "novo")[0], 1)

    def test_caracteres_de_controle_nao_chegam_ao_terminal(self):
        base = {"id": 1, "status": "pendente", "prioridade": "media",
                "criada_em": "2026-01-01T00:00:00", "data_limite": None}
        self._escrever([{**base, "descricao": "ok\x1b[31mRED\nlinha2"}], proximo_id=2)
        _, out, _ = self.rodar("list")
        self.assertNotIn("\x1b", out)
        self.assertEqual(len(out.strip().splitlines()), 3)

    def test_sem_arquivo_temporario_sobrando(self):
        self.rodar("add", "x")
        self.assertEqual([p.name for p in Path(self.dir.name).iterdir()], ["tasks.json"])


class TestHelp(BaseCli):
    def test_help_de_cada_comando(self):
        for cmd in ("add", "list", "done", "remove", "edit"):
            with self.subTest(cmd=cmd):
                codigo, out, _ = self.rodar(cmd, "--help")
                self.assertEqual(codigo, 0)
                self.assertIn("Exemplo:", out)


if __name__ == "__main__":
    unittest.main()
