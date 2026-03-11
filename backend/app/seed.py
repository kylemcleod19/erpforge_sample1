"""Seed script — creates sample products, components, BOMs, inventory, and work stations.

Run via: python -m app.seed   (or `make seed` with Docker)
"""
import logging
import sys
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models.product import (
    BOMRevision,
    Product,
    ProductBOMItem,
    ProductCompliance,
    ProductSpec,
)
from app.models.inventory import InventoryBalance
from app.models.manufacturing import ProductRouting, WorkStation

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def seed(db: Session) -> None:
    # Guard: skip if products already exist
    if db.query(Product).first():
        logger.info("Products already exist — skipping seed.")
        return

    # ------------------------------------------------------------------
    # Work Stations (shared across both assemblies)
    # ------------------------------------------------------------------
    stations = {
        "kitting": WorkStation(name="Kitting", description="Kit components for assembly", sequence=10),
        "mechanical_assy": WorkStation(name="Mechanical Assembly", description="Mechanical build and fastening", sequence=20),
        "smt_place": WorkStation(name="SMT Placement", description="Surface-mount component placement", sequence=30),
        "reflow": WorkStation(name="Reflow Soldering", description="Reflow oven soldering", sequence=40),
        "hand_solder": WorkStation(name="Hand Soldering", description="Through-hole and rework soldering", sequence=50),
        "test": WorkStation(name="Test & Inspection", description="Functional test and visual inspection", sequence=60),
        "final_assy": WorkStation(name="Final Assembly", description="Final integration and packaging", sequence=70),
    }
    for ws in stations.values():
        db.add(ws)
    db.flush()
    logger.info("Created %d work stations", len(stations))

    # ------------------------------------------------------------------
    # Helper to create products
    # ------------------------------------------------------------------
    products: dict[str, Product] = {}

    def p(
        sku: str,
        name: str,
        item_type: str,
        unit_cost: str = "0",
        unit_price: str = "0",
        uom: str = "EA",
        category: str | None = None,
        description: str | None = None,
        lifecycle: str = "production",
    ) -> Product:
        prod = Product(
            sku=sku,
            name=name,
            item_type=item_type,
            unit_cost=Decimal(unit_cost),
            unit_price=Decimal(unit_price),
            unit_of_measure=uom,
            category=category,
            description=description,
            lifecycle_status=lifecycle,
        )
        db.add(prod)
        db.flush()
        products[sku] = prod
        return prod

    # ------------------------------------------------------------------
    # 1.  MECHANICAL ASSEMBLY — Precision Linear Actuator (ASM-LA-100)
    # ------------------------------------------------------------------
    logger.info("--- Mechanical Assembly: Precision Linear Actuator ---")

    # Raw materials
    p("RAW-AL6061-BAR", "6061-T6 Aluminum Bar Stock", "raw_material",
      unit_cost="12.50", uom="KG", category="Metal Stock",
      description="6061-T6 aluminum bar, 25mm x 50mm profile")
    p("RAW-SS304-ROD", "304 Stainless Steel Rod", "raw_material",
      unit_cost="18.75", uom="KG", category="Metal Stock",
      description="304 SS precision ground rod, 12mm diameter")
    p("RAW-GREASE-NLGI2", "NLGI #2 Bearing Grease", "raw_material",
      unit_cost="22.00", uom="KG", category="Lubricant",
      description="Lithium-complex grease for linear bearings")

    # Components — mechanical
    p("CMP-LB-12", "Linear Ball Bearing 12mm", "component",
      unit_cost="8.45", category="Bearing",
      description="Closed-type linear ball bearing, 12mm bore, 21mm OD")
    p("CMP-ACME-12x2", "ACME Lead Screw 12x2mm", "component",
      unit_cost="14.30", category="Drive",
      description="ACME lead screw, 12mm dia, 2mm lead, 200mm travel, C3 accuracy")
    p("CMP-ACME-NUT-12", "ACME Lead Screw Nut", "component",
      unit_cost="6.80", category="Drive",
      description="Anti-backlash split nut for 12x2 ACME screw")
    p("CMP-COUPLER-6x8", "Shaft Coupler 6mm-8mm", "component",
      unit_cost="3.90", category="Coupling",
      description="Flexible jaw coupler, 6mm to 8mm bore")
    p("CMP-BRACKET-END", "End Plate Bracket", "component",
      unit_cost="4.20", category="Structural",
      description="Machined aluminum end plate, 4x M4 mounting holes")
    p("CMP-RAIL-12-200", "Linear Guide Rail 12x200mm", "component",
      unit_cost="11.60", category="Guide",
      description="Hardened steel linear rail, 12mm width, 200mm length")
    p("CMP-BOLT-M4x12", "M4x12 Socket Cap Bolt", "component",
      unit_cost="0.08", category="Fastener",
      description="ISO 4762 socket head cap screw, M4x12, A2 stainless")
    p("CMP-BOLT-M3x8", "M3x8 Socket Cap Bolt", "component",
      unit_cost="0.05", category="Fastener",
      description="ISO 4762 socket head cap screw, M3x8, A2 stainless")
    p("CMP-WASHER-M4", "M4 Flat Washer", "component",
      unit_cost="0.02", category="Fastener",
      description="DIN 125 flat washer, M4, A2 stainless")
    p("CMP-DOWEL-4x10", "Dowel Pin 4x10mm", "component",
      unit_cost="0.15", category="Fastener",
      description="ISO 2338 dowel pin, 4mm x 10mm, hardened steel")
    p("CMP-ORING-18x2", "O-Ring 18x2mm Viton", "component",
      unit_cost="0.35", category="Seal",
      description="FKM Viton O-ring, 18mm ID, 2mm cross-section")

    # Sub-assembly: carriage
    carriage = p("ASM-CARRIAGE-12", "Linear Carriage Assembly", "assembly",
                  unit_cost="32.00", unit_price="48.00", category="Subassembly",
                  description="Pre-assembled carriage with bearing blocks and mounting plate")

    # Top-level assembly: linear actuator
    actuator = p("ASM-LA-100", "Precision Linear Actuator 200mm", "finished_good",
                  unit_cost="95.00", unit_price="189.00", category="Motion",
                  description="Complete linear actuator, 200mm travel, 0.01mm repeatability")

    # BOM — Carriage sub-assembly (find numbers for mechanical)
    bom_carriage = [
        ("CMP-LB-12", 2, "EA", None, "1", "material", "Press-fit into carriage block"),
        ("CMP-BOLT-M3x8", 4, "EA", None, "2", "material", "Bearing retainer bolts"),
        ("CMP-ORING-18x2", 2, "EA", None, "3", "material", "Dust seals for bearing bores"),
        ("CMP-DOWEL-4x10", 2, "EA", None, "4", "material", "Alignment dowels"),
    ]
    for sku, qty, uom, ref, line, ctype, notes in bom_carriage:
        db.add(ProductBOMItem(
            parent_product_id=carriage.id,
            child_product_id=products[sku].id,
            quantity=Decimal(str(qty)),
            unit_of_measure=uom,
            reference_designator=ref,
            line_designator=line,
            component_type=ctype,
            notes=notes,
        ))

    # BOM — Top-level actuator
    bom_actuator = [
        ("ASM-CARRIAGE-12", 1, "EA", None, "1", "subassembly", "Carriage assembly"),
        ("CMP-ACME-12x2", 1, "EA", None, "2", "material", "Lead screw, cut to 220mm"),
        ("CMP-ACME-NUT-12", 1, "EA", None, "3", "material", "Mounted on carriage"),
        ("CMP-RAIL-12-200", 2, "EA", None, "4", "material", "Parallel guide rails"),
        ("CMP-BRACKET-END", 2, "EA", None, "5", "material", "Front and rear end plates"),
        ("CMP-COUPLER-6x8", 1, "EA", None, "6", "material", "Motor-to-screw coupler"),
        ("CMP-BOLT-M4x12", 8, "EA", None, "7", "material", "End plate mounting bolts"),
        ("CMP-WASHER-M4", 8, "EA", None, "8", "material", "Under bolt heads"),
        ("CMP-DOWEL-4x10", 4, "EA", None, "9", "material", "Rail alignment dowels"),
    ]
    for sku, qty, uom, ref, line, ctype, notes in bom_actuator:
        db.add(ProductBOMItem(
            parent_product_id=actuator.id,
            child_product_id=products[sku].id,
            quantity=Decimal(str(qty)),
            unit_of_measure=uom,
            reference_designator=ref,
            line_designator=line,
            component_type=ctype,
            notes=notes,
        ))

    # Routing for actuator
    for seq, station_key in enumerate([
        "kitting", "mechanical_assy", "test", "final_assy",
    ], start=1):
        db.add(ProductRouting(
            product_id=actuator.id,
            station_id=stations[station_key].id,
            sequence=seq,
        ))

    db.flush()
    logger.info("Created mechanical assembly: %s (%d BOM lines)", actuator.sku,
                len(bom_carriage) + len(bom_actuator))

    # ------------------------------------------------------------------
    # 2.  ELECTRICAL ASSEMBLY — Motor Controller PCB (ASM-MCTRL-200)
    # ------------------------------------------------------------------
    logger.info("--- Electrical Assembly: Motor Controller Board ---")

    # Components — electronic
    p("IC-STM32F405", "STM32F405RG Microcontroller", "component",
      unit_cost="4.85", category="IC",
      description="ARM Cortex-M4, 168MHz, 1MB Flash, LQFP-64")
    p("IC-DRV8301", "DRV8301 Motor Gate Driver", "component",
      unit_cost="3.20", category="IC",
      description="Three-phase gate driver with dual current shunt amps, HTSSOP-56")
    p("IC-LM5164", "LM5164 DC-DC Converter", "component",
      unit_cost="1.95", category="IC",
      description="36V input, 3.3V/0.5A output, SOT-23-6")
    p("IC-MCP2551", "MCP2551 CAN Transceiver", "component",
      unit_cost="0.82", category="IC",
      description="High-speed CAN transceiver, SOIC-8")

    p("FET-IRFH5015", "IRFH5015 N-Ch MOSFET", "component",
      unit_cost="0.95", category="Semiconductor",
      description="100V, 56A, 4.1mOhm, PQFN 5x6mm")

    p("RES-10K-0402", "10K Ohm Resistor 0402", "component",
      unit_cost="0.003", category="Passive",
      description="Thick film, 1%, 1/16W, 0402")
    p("RES-4K7-0402", "4.7K Ohm Resistor 0402", "component",
      unit_cost="0.003", category="Passive",
      description="Thick film, 1%, 1/16W, 0402")
    p("RES-100R-0402", "100 Ohm Resistor 0402", "component",
      unit_cost="0.003", category="Passive",
      description="Thick film, 1%, 1/16W, 0402")
    p("RES-0R01-2512", "10mOhm Shunt Resistor 2512", "component",
      unit_cost="0.18", category="Passive",
      description="Current sense, 1%, 1W, 2512")

    p("CAP-100NF-0402", "100nF Capacitor 0402", "component",
      unit_cost="0.005", category="Passive",
      description="MLCC, X7R, 25V, 0402")
    p("CAP-10UF-0805", "10uF Capacitor 0805", "component",
      unit_cost="0.02", category="Passive",
      description="MLCC, X5R, 25V, 0805")
    p("CAP-100UF-ELEC", "100uF Electrolytic 10x10mm", "component",
      unit_cost="0.35", category="Passive",
      description="Aluminum electrolytic, 50V, low-ESR, 10mm dia")

    p("IND-4U7-1210", "4.7uH Inductor 1210", "component",
      unit_cost="0.28", category="Passive",
      description="Shielded power inductor, 3A sat, 1210")

    p("CONN-JST-XH-6", "JST XH 6-Pin Header", "component",
      unit_cost="0.12", category="Connector",
      description="2.5mm pitch, vertical, through-hole")
    p("CONN-XT30-M", "XT30 Power Connector Male", "component",
      unit_cost="0.45", category="Connector",
      description="30A rated power connector, PCB mount")
    p("CONN-CAN-4P", "4-Pin CAN Bus Connector", "component",
      unit_cost="0.30", category="Connector",
      description="Molex Micro-Fit 3.0, 4-circuit, vertical")

    p("LED-GRN-0603", "Green LED 0603", "component",
      unit_cost="0.015", category="Optoelectronic",
      description="Green LED, 0603, 20mA, 2.0V")
    p("LED-RED-0603", "Red LED 0603", "component",
      unit_cost="0.015", category="Optoelectronic",
      description="Red LED, 0603, 20mA, 2.0V")

    p("XTAL-8MHZ", "8MHz Crystal HC49", "component",
      unit_cost="0.22", category="Passive",
      description="8MHz crystal, 20ppm, 18pF load, HC49/SMD")

    # Bare PCB
    pcb_bare = p("PCB-MCTRL-200", "Motor Controller PCB (bare)", "component",
                  unit_cost="2.80", category="PCB",
                  description="4-layer, 1.6mm, ENIG finish, 50x70mm, UL94V-0")

    # Top-level PCBA
    mctrl = p("ASM-MCTRL-200", "Motor Controller Board", "finished_good",
               unit_cost="28.00", unit_price="59.00", category="Electronics",
               description="3-phase brushless motor controller, 36V/15A, CAN bus, FOC firmware")

    # BOM — Motor controller PCBA (reference designators for electronics)
    bom_mctrl = [
        ("PCB-MCTRL-200", 1, "EA", None, None, "material", "Bare board"),
        ("IC-STM32F405", 1, "EA", "U1", None, "electronic", "Main MCU"),
        ("IC-DRV8301", 1, "EA", "U2", None, "electronic", "Gate driver"),
        ("IC-LM5164", 1, "EA", "U3", None, "electronic", "3.3V regulator"),
        ("IC-MCP2551", 1, "EA", "U4", None, "electronic", "CAN transceiver"),
        ("FET-IRFH5015", 6, "EA", "Q1-Q6", None, "electronic", "Half-bridge MOSFETs (3 phases)"),
        ("RES-10K-0402", 12, "EA", "R1-R12", None, "electronic", "Pull-up/pull-down resistors"),
        ("RES-4K7-0402", 4, "EA", "R13-R16", None, "electronic", "I2C pull-ups, voltage dividers"),
        ("RES-100R-0402", 6, "EA", "R17-R22", None, "electronic", "Gate resistors"),
        ("RES-0R01-2512", 3, "EA", "R23 R24 R25", None, "electronic", "Phase current shunts"),
        ("CAP-100NF-0402", 16, "EA", "C1-C16", None, "electronic", "Decoupling caps"),
        ("CAP-10UF-0805", 4, "EA", "C17-C20", None, "electronic", "Bulk decoupling"),
        ("CAP-100UF-ELEC", 2, "EA", "C21 C22", None, "electronic", "Bus capacitors"),
        ("IND-4U7-1210", 1, "EA", "L1", None, "electronic", "Buck converter inductor"),
        ("XTAL-8MHZ", 1, "EA", "Y1", None, "electronic", "MCU clock crystal"),
        ("CONN-JST-XH-6", 1, "EA", "J1", None, "electronic", "Hall sensor connector"),
        ("CONN-XT30-M", 1, "EA", "J2", None, "electronic", "Power input"),
        ("CONN-CAN-4P", 1, "EA", "J3", None, "electronic", "CAN bus connector"),
        ("LED-GRN-0603", 1, "EA", "D1", None, "electronic", "Power indicator"),
        ("LED-RED-0603", 1, "EA", "D2", None, "electronic", "Fault indicator"),
    ]
    for sku, qty, uom, ref, line, ctype, notes in bom_mctrl:
        db.add(ProductBOMItem(
            parent_product_id=mctrl.id,
            child_product_id=products[sku].id,
            quantity=Decimal(str(qty)),
            unit_of_measure=uom,
            reference_designator=ref,
            line_designator=line,
            component_type=ctype,
            notes=notes,
        ))

    # Routing for PCBA
    for seq, station_key in enumerate([
        "kitting", "smt_place", "reflow", "hand_solder", "test", "final_assy",
    ], start=1):
        db.add(ProductRouting(
            product_id=mctrl.id,
            station_id=stations[station_key].id,
            sequence=seq,
        ))

    db.flush()
    logger.info("Created electrical assembly: %s (%d BOM lines)", mctrl.sku, len(bom_mctrl))

    # ------------------------------------------------------------------
    # 3.  Approved BOM Revisions for both top-level products
    # ------------------------------------------------------------------
    from datetime import datetime

    for prod in [actuator, mctrl]:
        rev = BOMRevision(
            product_id=prod.id,
            revision_number=1,
            status="approved",
            notes="Initial release",
            approved_by="seed",
            approved_at=datetime.utcnow(),
        )
        db.add(rev)
    db.flush()
    logger.info("Created BOM revisions")

    # ------------------------------------------------------------------
    # 4.  Compliance records
    # ------------------------------------------------------------------
    db.add(ProductCompliance(
        product_id=mctrl.id, scope="product", cert_type="CE",
        cert_number="CE-2025-MCTRL-001",
        notes="EMC tested per EN 61000-6-3",
    ))
    db.add(ProductCompliance(
        product_id=mctrl.id, scope="product", cert_type="RoHS",
        notes="All components RoHS-3 compliant",
    ))
    db.add(ProductCompliance(
        product_id=actuator.id, scope="product", cert_type="CE",
        cert_number="CE-2025-LA-001",
        notes="Machinery directive 2006/42/EC",
    ))
    db.flush()
    logger.info("Created compliance records")

    # ------------------------------------------------------------------
    # 5.  Spec URLs
    # ------------------------------------------------------------------
    db.add(ProductSpec(product_id=actuator.id, label="Assembly Drawing", url="https://docs.example.com/LA-100-assy.pdf"))
    db.add(ProductSpec(product_id=actuator.id, label="Lead Screw Datasheet", url="https://docs.example.com/ACME-12x2.pdf"))
    db.add(ProductSpec(product_id=mctrl.id, label="Schematic", url="https://docs.example.com/MCTRL-200-sch.pdf"))
    db.add(ProductSpec(product_id=mctrl.id, label="Layout (Gerber)", url="https://docs.example.com/MCTRL-200-gerber.zip"))
    db.add(ProductSpec(product_id=mctrl.id, label="Firmware Source", url="https://git.example.com/mctrl-fw"))
    db.flush()
    logger.info("Created spec URLs")

    # ------------------------------------------------------------------
    # 6.  Starting inventory balances
    # ------------------------------------------------------------------
    inventory_seed = [
        # Mechanical components — decent stock
        ("CMP-LB-12", 50), ("CMP-ACME-12x2", 20), ("CMP-ACME-NUT-12", 25),
        ("CMP-COUPLER-6x8", 30), ("CMP-BRACKET-END", 40), ("CMP-RAIL-12-200", 30),
        ("CMP-BOLT-M4x12", 500), ("CMP-BOLT-M3x8", 500), ("CMP-WASHER-M4", 500),
        ("CMP-DOWEL-4x10", 200), ("CMP-ORING-18x2", 100),
        # Raw materials
        ("RAW-AL6061-BAR", 25), ("RAW-SS304-ROD", 15), ("RAW-GREASE-NLGI2", 5),
        # Electronic components
        ("IC-STM32F405", 100), ("IC-DRV8301", 80), ("IC-LM5164", 150),
        ("IC-MCP2551", 120), ("FET-IRFH5015", 300),
        ("RES-10K-0402", 5000), ("RES-4K7-0402", 3000), ("RES-100R-0402", 2000),
        ("RES-0R01-2512", 500),
        ("CAP-100NF-0402", 8000), ("CAP-10UF-0805", 2000), ("CAP-100UF-ELEC", 400),
        ("IND-4U7-1210", 300), ("XTAL-8MHZ", 200),
        ("CONN-JST-XH-6", 150), ("CONN-XT30-M", 100), ("CONN-CAN-4P", 100),
        ("LED-GRN-0603", 1000), ("LED-RED-0603", 1000),
        ("PCB-MCTRL-200", 50),
        # Finished sub-assemblies: small stock
        ("ASM-CARRIAGE-12", 5),
    ]
    for sku, qty in inventory_seed:
        db.add(InventoryBalance(
            product_id=products[sku].id,
            quantity_on_hand=Decimal(str(qty)),
        ))
    db.flush()
    logger.info("Created %d inventory balances", len(inventory_seed))

    # ------------------------------------------------------------------
    db.commit()
    logger.info("Seed complete. %d products created.", len(products))


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    except Exception:
        db.rollback()
        logger.exception("Seed failed")
        sys.exit(1)
    finally:
        db.close()
