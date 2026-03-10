# ERP / MRP BOM Discovery Questionnaire

This document contains discovery questions typically asked during
ERP/MRP implementations to understand how a manufacturer structures
products and bills of materials.\
No schema or architectural guidance is included; the purpose is purely
to gather requirements.

------------------------------------------------------------------------

# 1. Product Catalog Structure

1.  How many finished products does the business manufacture or sell?
2.  Are products grouped into families or categories?
3.  Do products share common assemblies or components?
4.  Are there platform products that other products derive from?
5.  Are products ever cloned or copied from existing products?
6.  Are products typically custom per customer order or standard SKUs?
7.  Can a product exist in multiple configurations?
8.  How are product identifiers defined (SKU, part number, internal ID)?
9.  Are product names or identifiers tied to revisions?
10. Does the organization distinguish between internal part numbers and
    customer-facing part numbers?

------------------------------------------------------------------------

# 2. BOM Structure

11. What levels of BOM hierarchy are typically used?
12. Are BOMs generally flat or multi-level?
13. Are assemblies reused across multiple products?
14. Can an assembly exist independently as a sellable item?
15. Can a component appear in multiple assemblies?
16. Are assemblies always built before final product assembly?
17. Are some assemblies logical groupings rather than physical units?
18. Are there items that appear on the BOM but are not stocked?
19. Should the BOM represent design structure, manufacturing structure,
    or both?
20. Do BOMs need to reflect packaging or shipping structure?

------------------------------------------------------------------------

# 3. Component Management

21. What types of components exist (mechanical, electronic, raw
    materials, etc.)?
22. Are components always purchased, always manufactured, or both?
23. Do components have approved vendor lists?
24. Can components have multiple interchangeable suppliers?
25. Can components have substitute parts?
26. Are substitutions approved automatically or manually?
27. Are some components proprietary or restricted?
28. Do components belong to categories or classifications?
29. Do components require documentation such as drawings or
    specifications?
30. Are component lifecycle states tracked (active, obsolete, etc.)?

------------------------------------------------------------------------

# 4. PCB / Electronics Specific (if applicable)

31. Are electronic components tracked by reference designator?
32. Are PCB assemblies treated as components or assemblies?
33. Are PCB revisions tied to BOM revisions?
34. Are alternate components allowed for electronic parts?
35. Are electronic components grouped by function or only by quantity?
36. Are firmware or software elements associated with assemblies?

------------------------------------------------------------------------

# 5. Revision and Change Management

37. How are BOM revisions tracked?
38. Are revisions numeric, alphabetic, or date-based?
39. Can multiple revisions exist simultaneously?
40. Are changes tracked through formal change orders?
41. Are changes approved before becoming active?
42. Are changes tied to production batches or serial ranges?
43. Should previous BOM revisions remain accessible?
44. Should the system record the reason for each change?

------------------------------------------------------------------------

# 6. Traceability

45. Which items require lot tracking?
46. Which items require serial number tracking?
47. Are finished products serialized?
48. Is traceability required for regulatory reasons?
49. Should traceability extend to subassemblies?
50. Should traceability include supplier information?

------------------------------------------------------------------------

# 7. Inventory and Consumables

51. Are some materials consumed in bulk rather than individually
    tracked?
52. Should consumables appear on the BOM?
53. Are consumables replenished through normal purchasing or separate
    processes?
54. Should the system estimate usage for bulk materials?
55. Are there materials used in production that should not appear on the
    BOM?

------------------------------------------------------------------------

# 8. Scrap and Overage

56. Should scrap factors be applied to components?
57. Are scrap rates defined per component, per category, or per process?
58. Should scrap be recorded during production?
59. Should the system automatically increase component quantities to
    account for scrap?
60. Are scrap rates expected to change over time?

------------------------------------------------------------------------

# 9. Configuration and Variants

61. Can products be configured with selectable options?
62. What types of options exist (size, color, voltage, etc.)?
63. Are configurations selected during order entry or during
    manufacturing planning?
64. Are variant products assigned separate SKUs?
65. Do variants inherit components from a base product?
66. Are configuration rules required to prevent invalid combinations?

------------------------------------------------------------------------

# 10. Manufacturing Context

67. Are products built in a single facility or multiple facilities?
68. Can the same product have different BOMs at different plants?
69. Are there location-specific components?
70. Are packaging materials included in the BOM?
71. Are tools or fixtures ever included in BOM structures?
72. Are there items required only during certain production steps?

------------------------------------------------------------------------

# 11. Product Lifecycle

73. Do products move through lifecycle stages (prototype, production,
    end-of-life)?
74. Can components become obsolete while products remain active?
75. Should the system prevent use of obsolete components?
76. Should historical production reference the BOM revision used at the
    time?

------------------------------------------------------------------------

# 12. Documentation and Metadata

77. Are engineering drawings linked to BOM items?
78. Are compliance documents required (RoHS, safety certifications,
    etc.)?
79. Should the system store manufacturing instructions alongside BOMs?
80. Are there notes or instructions specific to individual BOM lines?
