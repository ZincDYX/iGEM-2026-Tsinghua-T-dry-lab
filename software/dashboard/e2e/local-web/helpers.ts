import {expect,type Page} from '@playwright/test';
export async function ready(page:Page){await expect(page.getByLabel('Current project',{exact:true})).not.toHaveValue('');}
export async function rename(page:Page,name:string){await page.getByText('File',{exact:true}).click();await page.getByRole('menuitem',{name:'Rename project',exact:true}).click();await page.getByLabel('Project name').fill(name);await page.getByRole('button',{name:'Rename',exact:true}).click();}
export async function commitImport(page:Page){await expect(page.getByRole('button',{name:'Import objects',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Import objects',exact:true}).click();await expect(page.getByLabel('Import transaction preview')).toHaveCount(0);}
