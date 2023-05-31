import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

(async () => {
    puppeteer.use(StealthPlugin());
    const browser = await puppeteer.launch({
        // headless: false,
        // headless: 'new',
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

    await page.type('input[id=combo-box-demo]', 'http://localhost:390', { delay: 100 })
    //enter key on the same input
    await page.click('.MuiAutocomplete-listbox > li')


    //get button with class css-qzbt6i-MuiButtonBase-root-MuiIconButton-root-MuiAutocomplete-popupIndicator and click it 
    const button = await page.waitForSelector(
        '.css-nxo287-MuiInputBase-input-MuiOutlinedInput-input'
    );
    await button.click();

    await page.type('.css-1t8l2tu-MuiInputBase-input-MuiOutlinedInput-input', '0123456789abcdefghijk', { delay: 10 });

    // Wait and click on first result
    const searchResultSelector = '.css-sghohy-MuiButtonBase-root-MuiButton-root';
    await page.click(searchResultSelector);

    // page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    const inner_html = await page.evaluate(() => document.querySelector('button:disabled').innerHTML);



    const Closebutton = await page.$x("//button[contains(., 'Close')]");
    await Closebutton[0].click();

    //.css-1d6w9lk-MuiButtonBase-root-MuiIconButton-root 
    const bb = await page.$x("//button[@aria-label='menu']")
    await page.waitForTimeout(1000)
    await bb[0].click();



    const clientRoute = await page.$x("//li[contains(., 'Client')]");
    await page.waitForTimeout(1000)
    await clientRoute[0].click();
    console.log('here')
    if (browser.headless == false) {
        await page.waitForTimeout(5000) //wait for 5 seconds before closing
    }
    await browser.close();
    console.log(inner_html)

})();