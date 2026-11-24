export const FLEET_COLUMNS = [
  { field: "item_apolice", label: "Item", kind: "integer", width: 88 },
  { field: "placa", label: "Placa", kind: "text", width: 128 },
  { field: "marca", label: "Marca", kind: "text", width: 136 },
  { field: "modelo", label: "Modelo", kind: "text", width: 280 },
  { field: "ano_fabricacao", label: "Ano fab.", kind: "integer", width: 88 },
  { field: "ano_modelo", label: "Ano modelo", kind: "integer", width: 112 },
  { field: "chassi", label: "Chassi", kind: "text", width: 216 },
  { field: "classe_bonus", label: "Bônus", kind: "integer", width: 80 },
  { field: "codigo_fipe", label: "Código FIPE", kind: "text", width: 120 },
  { field: "valor_casco", label: "Franquia casco", kind: "money", width: 136 },
  { field: "rcf_danos_materiais", label: "RCF DM", kind: "money", width: 136 },
  { field: "rcf_danos_corporais", label: "RCF DC", kind: "money", width: 136 },
  { field: "danos_morais", label: "Danos morais", kind: "money", width: 136 },
  { field: "app_passageiros", label: "APP", kind: "money", width: 136 },
  { field: "cobertura_vidros", label: "Vidros", kind: "money", width: 136 },
  { field: "assistencia", label: "Assistência", kind: "text", width: 176 },
  { field: "codigo_identificacao", label: "C.I.", kind: "text", width: 160 },
] as const;

export type ColumnSpec = (typeof FLEET_COLUMNS)[number];
export type FleetField = ColumnSpec["field"];
export type FleetValue = string | number | null;
export type FleetVehicle = Record<FleetField, FleetValue> & {
  /** ID estável da sessão; não derive da placa, do item ou da posição filtrada. */
  id: string;
  flags_atencao: string[];
  issues?: Partial<Record<FleetField, string[]>>;
};

