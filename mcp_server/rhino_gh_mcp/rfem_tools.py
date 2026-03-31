"""Tools for interacting with RFEM 6 through SOAP/WebService API."""
from mcp.server.fastmcp import FastMCP
import logging
import os
import json
import traceback
from typing import Dict, Any, List, Optional

logger = logging.getLogger("RfemTools")


class RfemConnection:
    """Manages connection to RFEM 6 via SOAP/WebService (port 8081)."""

    def __init__(self, host='localhost', port=8081):
        self.host = os.environ.get('RFEM_HOST', host)
        self.port = int(os.environ.get('RFEM_PORT', port))
        self._connected = False

    def check_available(self) -> bool:
        """Check if RFEM WebService is available by fetching WSDL."""
        try:
            import requests
            r = requests.get(
                "http://{}:{}/wsdl".format(self.host, self.port),
                timeout=5
            )
            return r.status_code == 200
        except Exception:
            return False

    def connect(self, new_model=False, model_name=""):
        """Initialize RFEM Model connection via SOAP."""
        from RFEM.initModel import Model
        Model(new_model, model_name)
        self._connected = True

    def disconnect(self):
        """Close RFEM connection."""
        if self._connected:
            try:
                from RFEM.initModel import Model
                Model.clientModel.service.close_connection()
            except Exception:
                pass
            self._connected = False

    def ensure_connected(self):
        """Ensure we have an active connection to RFEM."""
        if not self._connected:
            self.connect()


# Singleton pattern
_rfem_connection = None


def get_rfem_connection() -> RfemConnection:
    global _rfem_connection
    if _rfem_connection is None:
        _rfem_connection = RfemConnection()
    return _rfem_connection


def _serialize(obj) -> Any:
    """Convert RFEM SOAP objects to JSON-serializable dicts."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):
                result[key] = _serialize(value)
        return result
    if hasattr(obj, '__iter__'):
        return [_serialize(item) for item in obj]
    return str(obj)


class RfemTools:
    """RFEM 6 WebService tools for structural engineering via MCP."""

    def __init__(self, app: FastMCP):
        self.app = app
        self._register_tools()

    def _register_tools(self):
        self.app.tool()(self.rfem_check_connection)
        self.app.tool()(self.rfem_get_model_info)
        self.app.tool()(self.rfem_get_nodes)
        self.app.tool()(self.rfem_set_node)
        self.app.tool()(self.rfem_get_members)
        self.app.tool()(self.rfem_set_member)
        self.app.tool()(self.rfem_get_materials)
        self.app.tool()(self.rfem_set_material)
        self.app.tool()(self.rfem_get_sections)
        self.app.tool()(self.rfem_set_section)
        self.app.tool()(self.rfem_set_nodal_support)
        self.app.tool()(self.rfem_set_load_case)
        self.app.tool()(self.rfem_set_nodal_load)
        self.app.tool()(self.rfem_calculate)
        self.app.tool()(self.rfem_get_results)
        self.app.tool()(self.rfem_update_members_section)
        self.app.tool()(self.rfem_create_member_group)
        self.app.tool()(self.rfem_get_member_groups)
        self.app.tool()(self.rfem_update_group_section)
        self.app.tool()(self.rfem_execute_code)

    def rfem_check_connection(self) -> str:
        """Check if RFEM WebService is available and connectable.

        Returns connection status and RFEM model info if available.
        """
        conn = get_rfem_connection()
        wsdl_ok = conn.check_available()
        if not wsdl_ok:
            return json.dumps({
                "status": "error",
                "message": "RFEM WebService not available at http://{}:{}. "
                           "Enable it in RFEM: Options > Program Options > WebService I".format(
                               conn.host, conn.port)
            })
        try:
            conn.connect()
            return json.dumps({
                "status": "connected",
                "host": conn.host,
                "port": conn.port,
                "message": "Successfully connected to RFEM WebService"
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": "WSDL available but connection failed: {}".format(str(e))
            })

    def rfem_get_model_info(self) -> str:
        """Get overview of the current RFEM model.

        Returns counts of nodes, members, surfaces, materials, sections, load cases, etc.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            info = {}
            try:
                info["nodes_count"] = client.service.get_object_count("E_OBJECT_TYPE_NODE", 0)
            except Exception:
                info["nodes_count"] = 0
            try:
                info["members_count"] = client.service.get_object_count("E_OBJECT_TYPE_MEMBER", 0)
            except Exception:
                info["members_count"] = 0
            try:
                info["surfaces_count"] = client.service.get_object_count("E_OBJECT_TYPE_SURFACE", 0)
            except Exception:
                info["surfaces_count"] = 0
            try:
                info["materials_count"] = client.service.get_object_count("E_OBJECT_TYPE_MATERIAL", 0)
            except Exception:
                info["materials_count"] = 0
            try:
                info["sections_count"] = client.service.get_object_count("E_OBJECT_TYPE_SECTION", 0)
            except Exception:
                info["sections_count"] = 0
            try:
                info["load_cases_count"] = client.service.get_object_count("E_OBJECT_TYPE_LOAD_CASE", 0)
            except Exception:
                info["load_cases_count"] = 0

            return json.dumps({"status": "success", "model_info": info})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_get_nodes(self, node_ids: Optional[List[int]] = None) -> str:
        """Get nodes from the RFEM model.

        Args:
            node_ids: List of specific node IDs to retrieve. If None, returns all nodes.

        Returns node coordinates (no, x, y, z) and properties.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            nodes = []
            if node_ids:
                ids = node_ids
            else:
                count = client.service.get_object_count("E_OBJECT_TYPE_NODE", 0)
                ids = range(1, count + 1)

            for nid in ids:
                try:
                    node = client.service.get_node(nid)
                    nodes.append(_serialize(node))
                except Exception:
                    continue

            return json.dumps({"status": "success", "nodes": nodes, "count": len(nodes)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_node(self, no: int, x: float, y: float, z: float) -> str:
        """Create or update a node in the RFEM model.

        Args:
            no: Node number (ID)
            x: X coordinate [m]
            y: Y coordinate [m]
            z: Z coordinate [m]
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.BasicObjects.node import Node
            Node(no, x, y, z)
            return json.dumps({"status": "success", "message": "Node {} set at ({}, {}, {})".format(no, x, y, z)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_get_members(self, member_ids: Optional[List[int]] = None) -> str:
        """Get members from the RFEM model.

        Args:
            member_ids: List of specific member IDs to retrieve. If None, returns all members.

        Returns member properties (no, start_node, end_node, section, type, length).
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            members = []
            if member_ids:
                ids = member_ids
            else:
                count = client.service.get_object_count("E_OBJECT_TYPE_MEMBER", 0)
                ids = range(1, count + 1)

            for mid in ids:
                try:
                    member = client.service.get_member(mid)
                    members.append(_serialize(member))
                except Exception:
                    continue

            return json.dumps({"status": "success", "members": members, "count": len(members)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_member(self, no: int, start_node: int, end_node: int,
                        start_section_no: int = 1, end_section_no: int = 0) -> str:
        """Create or update a member (beam/column) in the RFEM model.

        Args:
            no: Member number (ID)
            start_node: Start node number
            end_node: End node number
            start_section_no: Section number (default: 1)
            end_section_no: End section number (0 = same as start)
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.BasicObjects.member import Member
            Member(no, start_node, end_node, 0.0,
                   start_section_no, end_section_no if end_section_no > 0 else start_section_no)
            return json.dumps({
                "status": "success",
                "message": "Member {} set from node {} to node {}".format(no, start_node, end_node)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_get_materials(self, material_ids: Optional[List[int]] = None) -> str:
        """Get materials defined in the RFEM model.

        Args:
            material_ids: List of specific material IDs. If None, returns all materials.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            materials = []
            if material_ids:
                ids = material_ids
            else:
                count = client.service.get_object_count("E_OBJECT_TYPE_MATERIAL", 0)
                ids = range(1, count + 1)

            for mid in ids:
                try:
                    mat = client.service.get_material(mid)
                    materials.append(_serialize(mat))
                except Exception:
                    continue

            return json.dumps({"status": "success", "materials": materials, "count": len(materials)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_material(self, no: int, name: str) -> str:
        """Create or update a material in the RFEM model.

        Args:
            no: Material number (ID)
            name: Material name from RFEM library (e.g., "S235", "S355", "C25/30", "Timber C24")
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.BasicObjects.material import Material
            Material(no, name)
            return json.dumps({
                "status": "success",
                "message": "Material {} set: {}".format(no, name)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_get_sections(self, section_ids: Optional[List[int]] = None) -> str:
        """Get cross-sections defined in the RFEM model.

        Args:
            section_ids: List of specific section IDs. If None, returns all sections.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            sections = []
            if section_ids:
                ids = section_ids
            else:
                count = client.service.get_object_count("E_OBJECT_TYPE_SECTION", 0)
                ids = range(1, count + 1)

            for sid in ids:
                try:
                    sec = client.service.get_section(sid)
                    sections.append(_serialize(sec))
                except Exception:
                    continue

            return json.dumps({"status": "success", "sections": sections, "count": len(sections)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_section(self, no: int, name: str, material_no: int = 1) -> str:
        """Create or update a cross-section in the RFEM model.

        Args:
            no: Section number (ID)
            name: Section name from RFEM library (e.g., "IPE 300", "HEA 200", "RHS 200x100x10")
            material_no: Material number to assign (default: 1)
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.BasicObjects.section import Section
            Section(no, name, material_no)
            return json.dumps({
                "status": "success",
                "message": "Section {} set: {} (material {})".format(no, name, material_no)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_nodal_support(self, no: int, node_ids: str,
                               spring_x: float = 0.0, spring_y: float = 0.0,
                               spring_z: float = 0.0,
                               rotational_x: float = 0.0, rotational_y: float = 0.0,
                               rotational_z: float = 0.0) -> str:
        """Create a nodal support (boundary condition).

        Use 0.0 for free, inf for fixed. Common cases:
        - Pinned support: spring_x=inf, spring_y=inf, spring_z=inf, all rotational=0
        - Fixed support: all values = inf

        Args:
            no: Support number (ID)
            node_ids: Node numbers as string, e.g. "1 3 5" or "1-5"
            spring_x: Translational spring in X [N/m] (inf = fixed, 0 = free)
            spring_y: Translational spring in Y [N/m]
            spring_z: Translational spring in Z [N/m]
            rotational_x: Rotational spring about X [Nm/rad]
            rotational_y: Rotational spring about Y [Nm/rad]
            rotational_z: Rotational spring about Z [Nm/rad]
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.TypesForNodes.nodalSupport import NodalSupport
            conditions = [spring_x, spring_y, spring_z,
                          rotational_x, rotational_y, rotational_z]
            NodalSupport(no, node_ids, NodalSupport.StandardValueType(conditions))
            return json.dumps({
                "status": "success",
                "message": "Nodal support {} set on nodes: {}".format(no, node_ids)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_load_case(self, no: int, name: str,
                           self_weight_active: bool = False,
                           self_weight_direction: str = "z") -> str:
        """Create a load case.

        Args:
            no: Load case number (ID)
            name: Load case name (e.g., "Dead Load", "Live Load", "Wind")
            self_weight_active: Whether to include self-weight
            self_weight_direction: Direction of self-weight ("x", "y", or "z")
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.LoadCasesAndCombinations.loadCase import LoadCase
            from RFEM.LoadCasesAndCombinations.staticAnalysisSettings import StaticAnalysisSettings

            # Ensure static analysis settings exist
            try:
                from RFEM.initModel import Model
                Model.clientModel.service.get_static_analysis_settings(1)
            except Exception:
                StaticAnalysisSettings(1, 'Linear')

            sw_params = [self_weight_active]
            if self_weight_active:
                sw = [0.0, 0.0, 0.0]
                idx = {"x": 0, "y": 1, "z": 2}.get(self_weight_direction.lower(), 2)
                sw[idx] = 1.0
                sw_params.extend(sw)

            LoadCase(no, name, sw_params)
            return json.dumps({
                "status": "success",
                "message": "Load case {} created: {}".format(no, name)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_set_nodal_load(self, no: int, load_case_no: int, node_ids: str,
                            force_x: float = 0.0, force_y: float = 0.0,
                            force_z: float = 0.0) -> str:
        """Apply a nodal load (force) to nodes in a load case.

        Args:
            no: Load number (ID, unique within the load case)
            load_case_no: Load case number to apply the load in
            node_ids: Node numbers as string, e.g. "2" or "2 4 6"
            force_x: Force in X direction [N]
            force_y: Force in Y direction [N]
            force_z: Force in Z direction [N] (positive = downward in RFEM convention)
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.Loads.nodalLoad import NodalLoad
            NodalLoad(no, load_case_no, node_ids,
                      NodalLoad.ForceType(force_x, force_y, force_z))
            return json.dumps({
                "status": "success",
                "message": "Nodal load {} in LC{} applied on nodes: {} ({}, {}, {}) N".format(
                    no, load_case_no, node_ids, force_x, force_y, force_z)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_calculate(self, load_cases: Optional[List[int]] = None) -> str:
        """Correr el cálculo en RFEM.

        Args:
            load_cases: Lista de números de caso de carga a calcular.
                        Si es None, calcula todos los casos de carga.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            if load_cases:
                # Calcular casos específicos
                for lc in load_cases:
                    client.service.calculate_specific(lc)
            else:
                # Calcular todo
                client.service.calculate_all()

            return json.dumps({
                "status": "success",
                "message": "Cálculo ejecutado correctamente"
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_get_results(self, load_case_no: int = 1,
                         result_type: str = "members") -> str:
        """Leer resultados del cálculo para un caso de carga.

        Args:
            load_case_no: Número de caso de carga (default: 1)
            result_type: Tipo de resultado:
                - "members": Esfuerzos internos de barras (N, V, M) y ratios
                - "nodes": Desplazamientos nodales
                - "summary": Resumen general (máx. desplazamiento, máx. esfuerzos)
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            if result_type == "nodes":
                count = client.service.get_object_count("E_OBJECT_TYPE_NODE", 0)
                results = []
                for i in range(1, count + 1):
                    try:
                        res = client.service.get_results_for_nodes_in_load_cases(
                            load_case_no, i)
                        results.append(_serialize(res))
                    except Exception:
                        continue
                return json.dumps({
                    "status": "success",
                    "result_type": "nodes",
                    "load_case": load_case_no,
                    "results": results
                })

            elif result_type == "members":
                count = client.service.get_object_count("E_OBJECT_TYPE_MEMBER", 0)
                results = []
                for i in range(1, count + 1):
                    try:
                        res = client.service.get_results_for_members_internal_forces(
                            load_case_no, i)
                        member_info = client.service.get_member(i)
                        results.append({
                            "member_no": i,
                            "section": _serialize(getattr(member_info, 'section_start', None)),
                            "internal_forces": _serialize(res)
                        })
                    except Exception:
                        continue
                return json.dumps({
                    "status": "success",
                    "result_type": "members",
                    "load_case": load_case_no,
                    "results": results
                })

            elif result_type == "summary":
                # Resumen: buscar máximos
                summary = {
                    "load_case": load_case_no,
                    "max_displacement": None,
                    "max_member_forces": None
                }

                # Desplazamientos máximos
                node_count = client.service.get_object_count("E_OBJECT_TYPE_NODE", 0)
                max_disp = 0.0
                max_disp_node = None
                for i in range(1, node_count + 1):
                    try:
                        res = client.service.get_results_for_nodes_in_load_cases(
                            load_case_no, i)
                        res_data = _serialize(res)
                        if isinstance(res_data, dict):
                            for key in ['displacement_x', 'displacement_y', 'displacement_z',
                                        'ux', 'uy', 'uz']:
                                val = res_data.get(key)
                                if val is not None and abs(float(val)) > abs(max_disp):
                                    max_disp = float(val)
                                    max_disp_node = i
                    except Exception:
                        continue
                summary["max_displacement"] = {
                    "value_m": max_disp,
                    "node": max_disp_node
                }

                return json.dumps({"status": "success", "summary": summary})
            else:
                return json.dumps({
                    "status": "error",
                    "message": "result_type debe ser 'members', 'nodes' o 'summary'"
                })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_update_members_section(self, new_section_no: int,
                                     member_ids: Optional[List[int]] = None,
                                     current_section_no: Optional[int] = None) -> str:
        """Cambiar la sección de barras existentes. Ideal para iteración de diseño.

        Podés filtrar por lista de barras o por sección actual. Ejemplos de uso:
        - "Pasame todas las IPE 300 (sección 2) a IPE 400 (sección 3)"
        - "Cambiá las barras 5, 8 y 12 a la sección 4"

        Args:
            new_section_no: Número de la nueva sección a asignar
            member_ids: Lista de IDs de barras a modificar (ej: [1, 5, 8]).
                        Si es None, usa current_section_no para filtrar.
            current_section_no: Número de sección actual para filtrar.
                                Modifica TODAS las barras que tengan esta sección.
                                Se ignora si member_ids está definido.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            count = client.service.get_object_count("E_OBJECT_TYPE_MEMBER", 0)
            modified = []

            if member_ids:
                # Modificar barras específicas
                targets = member_ids
            elif current_section_no is not None:
                # Buscar barras con la sección actual
                targets = []
                for i in range(1, count + 1):
                    try:
                        member = client.service.get_member(i)
                        sec = getattr(member, 'section_start', None)
                        if sec is not None and int(sec) == current_section_no:
                            targets.append(i)
                    except Exception:
                        continue
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Necesitás pasar member_ids o current_section_no"
                })

            # Aplicar el cambio
            for mid in targets:
                try:
                    member = client.service.get_member(mid)
                    member.section_start = new_section_no
                    member.section_end = new_section_no
                    client.service.set_member(member)
                    modified.append(mid)
                except Exception as e:
                    logger.warning("Error modificando barra {}: {}".format(mid, str(e)))
                    continue

            return json.dumps({
                "status": "success",
                "message": "Se modificaron {} barras a sección {}".format(
                    len(modified), new_section_no),
                "modified_members": modified,
                "total_modified": len(modified)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_create_member_group(self, no: int, name: str, member_ids: str) -> str:
        """Crear un grupo de barras (Member Set) con un nombre.

        Los grupos son arbitrarios: las barras NO necesitan estar conectadas.
        Podés agrupar por ejemplo todas las columnas del piso 1, o todas las
        vigas en dirección X, etc.

        Después usá rfem_update_group_section() para cambiar la sección
        de todo el grupo de una.

        Args:
            no: Número del grupo (ID único)
            name: Nombre descriptivo (ej: "Columnas Piso 1", "Vigas dir X")
            member_ids: Números de barras separados por espacio (ej: "1 3 5 7 12")
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            # Crear el Member Set como tipo GROUP (barras no conectadas)
            member_set = client.factory.create('ns0:member_set')
            member_set.no = no
            member_set.members = member_ids
            member_set.set_type = "SET_TYPE_GROUP"
            member_set.name = name

            client.service.set_member_set(member_set)

            return json.dumps({
                "status": "success",
                "message": "Grupo '{}' (#{}) creado con barras: {}".format(name, no, member_ids)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_get_member_groups(self) -> str:
        """Listar todos los grupos de barras (Member Sets) del modelo.

        Devuelve nombre, número y barras de cada grupo.
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            count = client.service.get_object_count("E_OBJECT_TYPE_MEMBER_SET", 0)
            groups = []
            for i in range(1, count + 1):
                try:
                    ms = client.service.get_member_set(i)
                    groups.append({
                        "no": i,
                        "name": getattr(ms, 'name', ''),
                        "members": getattr(ms, 'members', ''),
                        "set_type": getattr(ms, 'set_type', ''),
                    })
                except Exception:
                    continue

            return json.dumps({
                "status": "success",
                "groups": groups,
                "count": len(groups)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_update_group_section(self, group_no: int, new_section_no: int) -> str:
        """Cambiar la sección de TODAS las barras de un grupo.

        Ejemplo: "A todo el grupo 'Columnas Piso 1' subile la sección a HEA 300"

        Args:
            group_no: Número del grupo (Member Set)
            new_section_no: Número de la nueva sección a asignar
        """
        conn = get_rfem_connection()
        conn.ensure_connected()
        try:
            from RFEM.initModel import Model
            client = Model.clientModel

            # Obtener el grupo y sus barras
            ms = client.service.get_member_set(group_no)
            group_name = getattr(ms, 'name', 'Grupo {}'.format(group_no))
            members_str = getattr(ms, 'members', '')

            if not members_str:
                return json.dumps({
                    "status": "error",
                    "message": "Grupo {} está vacío".format(group_no)
                })

            # Parsear IDs de barras del string (formato: "1 3 5 7" o "1-5")
            member_ids = []
            for part in str(members_str).split():
                if '-' in part:
                    start, end = part.split('-')
                    member_ids.extend(range(int(start), int(end) + 1))
                else:
                    member_ids.append(int(part))

            # Aplicar cambio de sección a cada barra
            modified = []
            for mid in member_ids:
                try:
                    member = client.service.get_member(mid)
                    member.section_start = new_section_no
                    member.section_end = new_section_no
                    client.service.set_member(member)
                    modified.append(mid)
                except Exception as e:
                    logger.warning("Error modificando barra {}: {}".format(mid, str(e)))
                    continue

            return json.dumps({
                "status": "success",
                "message": "Grupo '{}': {} barras cambiadas a sección {}".format(
                    group_name, len(modified), new_section_no),
                "group_name": group_name,
                "modified_members": modified,
                "total_modified": len(modified)
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rfem_execute_code(self, code: str) -> str:
        """Execute arbitrary Python code with RFEM library imports pre-loaded.

        This is the most powerful tool — use it for complex operations like:
        - Creating surfaces (plates, walls, shells)
        - Applying member loads or surface loads
        - Running calculations and retrieving results
        - Batch operations (multiple nodes/members in one call)
        - Any RFEM operation not covered by dedicated tools

        The code runs with these imports available:
        - RFEM.initModel (Model, clientModel)
        - RFEM.BasicObjects (Node, Member, Material, Section, Surface, Line)
        - RFEM.LoadCasesAndCombinations (LoadCase, StaticAnalysisSettings)
        - RFEM.Loads (NodalLoad, MemberLoad)
        - RFEM.TypesForNodes (NodalSupport)

        Use 'result = ...' to return data from the code.

        Args:
            code: Python code to execute with RFEM library
        """
        conn = get_rfem_connection()
        conn.ensure_connected()

        # Pre-loaded imports template
        preamble = """
from RFEM.initModel import Model
from RFEM.BasicObjects.material import Material
from RFEM.BasicObjects.section import Section
from RFEM.BasicObjects.node import Node
from RFEM.BasicObjects.member import Member
from RFEM.BasicObjects.line import Line
from RFEM.BasicObjects.surface import Surface
from RFEM.LoadCasesAndCombinations.loadCase import LoadCase
from RFEM.LoadCasesAndCombinations.staticAnalysisSettings import StaticAnalysisSettings
from RFEM.Loads.nodalLoad import NodalLoad
from RFEM.Loads.memberLoad import MemberLoad
from RFEM.TypesForNodes.nodalSupport import NodalSupport
from RFEM.enums import *
import math

clientModel = Model.clientModel
result = None
"""
        full_code = preamble + "\n" + code

        local_vars = {}
        try:
            exec(full_code, {}, local_vars)
            result = local_vars.get("result", None)
            if result is not None:
                result = _serialize(result)
            return json.dumps({
                "status": "success",
                "result": result,
                "message": "Code executed successfully"
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })
