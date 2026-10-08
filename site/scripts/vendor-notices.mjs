import fs from 'node:fs/promises';
import path from 'node:path';

// Include upstream notices with the built site. This deliberately inventories
// installed build dependencies too; it does not imply every package ships as
// browser code or impose a single license on unrelated scientific artifacts.
export async function writeVendorNotices(site, destination) {
  const lock=JSON.parse(await fs.readFile(path.join(site,'package-lock.json'),'utf8'));
  const sections=['Allagma documentation dependency notices\n\nGenerated from the locked, installed Node toolchain. This includes build-time dependencies as well as browser assets. Package license declarations and shipped notice text are reproduced below. Allagma core and study-specific licenses are documented separately.\n'];
  const covered=new Set();
  for (const entry of Object.keys(lock.packages).sort()) {
    if (!entry.startsWith('node_modules/')) continue;
    const directory=path.join(site,entry);
    let pkg, names;
    try {pkg=JSON.parse(await fs.readFile(path.join(directory,'package.json'),'utf8')); names=await fs.readdir(directory);}
    catch {continue;} // Platform-specific optional packages may be absent.
    const licenses=names.filter(n=>/^(licen[cs]e|copying|notice)(\.|$)/i.test(n));
    const blocks=[];
    for(const name of licenses.sort()) {
      const file=path.join(directory,name);
      if((await fs.stat(file)).isFile()) blocks.push(name+'\n'+await fs.readFile(file,'utf8'));
    }
    if(!blocks.length && ['pagefind','@pagefind/default-ui'].includes(pkg.name)) {
      if(pkg.version!=='1.5.2') throw new Error('Update and verify the pinned Pagefind notice for '+pkg.version);
      blocks.push('Upstream LICENSE (v1.5.2; omitted from the npm package)\n'+await fs.readFile(path.join(site,'licenses/pagefind-1.5.2.txt'),'utf8'));
      if(pkg.name==='@pagefind/default-ui') blocks.push('Svelte MIT notice for the bundled UI runtime (declared dependency range ^4.2.1)\n'+await fs.readFile(path.join(site,'licenses/svelte-4.2.1.txt'),'utf8'));
    }
    if(blocks.length) covered.add(pkg.name);
    sections.push(`\n${'='.repeat(72)}\n${pkg.name} ${pkg.version}\nLicense declaration: ${JSON.stringify(pkg.license||pkg.licenses||'See package source')}\nRepository: ${typeof pkg.repository==='string'?pkg.repository:pkg.repository?.url||pkg.homepage||''}\n\n${blocks.length?blocks.join('\n\n'):'No standalone notice file is shipped at this package root; consult the declared package source.'}\n`);
  }
  for(const required of ['astro','@astrojs/starlight','pagefind','@pagefind/default-ui']) {
    if(!covered.has(required)) throw new Error(`Missing shipped documentation notice: ${required}`);
  }
  await fs.writeFile(destination,sections.join('\n'));
  console.log(`Included ${covered.size} packages with shipped notices in the site.`);
}
