import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

(async () => {
    puppeteer.use(StealthPlugin());
    const browser = await puppeteer.launch({
        headless: false,
        // headless: 'new',
        devtools: true,
    });
    const page = await browser.newPage();



    // await page.goto('http://localhost:5173');
    // const button = await page.$x("//button[contains(., 'Agent State')]");
    // await button[0].click();

    // await page.screenshot({ path: 'stealth.png', fullPage: true })

    // const p = await page.$x("//p[contains(., 'Client')]");
    // const text = await page.evaluate(el => el.textContent, p[0]);
    // console.log(text)

    //open modal

    await page.goto('http://localhost:5173');
    await page.setCacheEnabled(false);

    //open modal
    await page.click('.css-9b1tbl-MuiButtonBase-root-MuiButton-root')
    //fill beginning of url
    await page.type('input[id=combo-box-demo]', 'https:', { delay: 100 })
    //enter key on the same input 
    await page.click('.MuiAutocomplete-listbox > li')
    //fill passcode
    await page.type('.css-1t8l2tu-MuiInputBase-input-MuiOutlinedInput-input', '0123456789abcdefghijk', { delay: 10 });

    // click on the connect butto
    const searchResultSelector = '.css-sghohy-MuiButtonBase-root-MuiButton-root';
    await page.click(searchResultSelector);

    // page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    //STATUS: CONNECTED 
    const inner_html = await page.evaluate(() => document.querySelector('button:disabled').innerHTML);
    //closte button 
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'connecting.png', fullPage: true })

    const Closebutton = await page.$x("//button[contains(., 'Close')]");
    await Closebutton[0].click();
    //getting the menu button
    const bb = await page.$x("//button[@aria-label='menu']")
    await page.waitForTimeout(1000)
    //clicking the menu button
    await bb[0].click();
    //get client route
    const clientRoute = await page.$x("//li[contains(., 'Client')]");
    await page.waitForTimeout(1000)
    await clientRoute[0].click();

    console.log('going to identifiers')
    await page.waitForTimeout(2000) //wait for 5 seconds before closing
    //getting the menu button
    await page.screenshot({ path: 'client.png', fullPage: true })

    const bb1 = await page.$x("//button[@aria-label='menu']")
    //clicking the menu button
    await bb1[0].click();
    await page.waitForTimeout(1000)
    //get identifiers route
    const IdentifiersRoute = await page.$x("//li[contains(., 'Ident')]");
    //click identifiers route
    await IdentifiersRoute[0].click();
    await page.waitForTimeout(1000)
    //create new identifier
    const add = await page.$x("//button[@aria-label='add']")
    await add[0].click();
    await page.waitForTimeout(2000)


    //rotate first identifier
    const rotates = await page.$x("//button[contains(., 'Rotate')]");
    await rotates[1].click(); 
    await page.waitForTimeout(5000)
    await page.screenshot({ path: 'identifier.png', fullPage: true })

    //close button
    await browser.close();
    console.log(inner_html)

})();