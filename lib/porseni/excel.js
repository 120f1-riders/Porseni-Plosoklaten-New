import * as XLSX from 'xlsx'

export const IMPORT_HEADERS = ['Nama Lengkap', 'Jenis Kelamin (L/P)', 'NISN', 'Tempat, Tanggal Lahir', 'Cabang Lomba']

// Generate & download an Excel template for bulk participant registration
export function downloadPesertaTemplate(lombaList = []) {
  const wb = XLSX.utils.book_new()

  // Sheet 1: Data Peserta (form to fill)
  const example = [
    IMPORT_HEADERS,
    ['Ahmad Fauzi', 'L', '0012345678', 'Kediri, 01 Januari 2015', lombaList[0]?.name || 'Kaligrafi'],
    ['Siti Aminah', 'P', '0012345679', 'Kediri, 05 Februari 2015', lombaList[0]?.name || 'Kaligrafi'],
  ]
  const ws = XLSX.utils.aoa_to_sheet(example)
  ws['!cols'] = [{ wch: 26 }, { wch: 18 }, { wch: 16 }, { wch: 28 }, { wch: 24 }]
  XLSX.utils.book_append_sheet(wb, ws, 'Data Peserta')

  // Sheet 2: reference list of available lomba
  const ref = [['Daftar Cabang Lomba Tersedia'], ['Nama Lomba', 'Kategori', 'Jenis']]
  lombaList.forEach((l) => ref.push([l.name, l.category, l.type === 'kelompok' ? 'Kelompok' : 'Individu']))
  const wsRef = XLSX.utils.aoa_to_sheet(ref)
  wsRef['!cols'] = [{ wch: 28 }, { wch: 14 }, { wch: 14 }]
  XLSX.utils.book_append_sheet(wb, wsRef, 'Referensi Lomba')

  XLSX.writeFile(wb, 'Template_Pendaftaran_Porseni.xlsx')
}

// Parse an uploaded Excel/CSV file -> array of row objects
export async function parsePesertaWorkbook(file) {
  const buf = await file.arrayBuffer()
  const wb = XLSX.read(buf, { type: 'array' })
  const ws = wb.Sheets[wb.SheetNames[0]]
  const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
  const out = []
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i]
    if (!r || r.every((c) => String(c).trim() === '')) continue
    const name = String(r[0] || '').trim()
    if (!name) continue
    let g = String(r[1] || '').trim().toUpperCase()
    if (g.startsWith('L')) g = 'L'
    else if (g.startsWith('P')) g = 'P'
    else g = ''
    out.push({
      participant_name: name,
      gender: g,
      nisn: String(r[2] || '').trim(),
      ttl: String(r[3] || '').trim(),
      lomba_name: String(r[4] || '').trim(),
    })
  }
  return out
}
